import io
from datetime import date, datetime

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka import FromDishka

from entities.checklist.enums import ChecklistAnswerValue
from entities.user.models import User
from services.checklist import ChecklistFlowService
from services.employee_import import EmployeeImportService
from services.telegram import TelegramService
from shared.enums.group import Group
from telegram.callback_data.admin import AdminMenuCallback
from telegram.keyboards.admin import admin_menu_keyboard
from telegram.keyboards.checklist import remove_keyboard
from telegram.middlewares.filters.chat import ChatTypeFilter
from telegram.middlewares.filters.permissions import GroupFilter
from telegram.states.admin import AdminStates
from core.logs import logger


router = Router()

ANSWER_LABELS: dict[ChecklistAnswerValue, str] = {
    ChecklistAnswerValue.YES: "Да",
    ChecklistAnswerValue.NO: "Нет",
    ChecklistAnswerValue.NOT_APPLICABLE: "Не применимо",
}


@router.message(
    Command("admin"),
    GroupFilter(Group.ADMIN),
    ChatTypeFilter(ChatType.PRIVATE),
)
async def admin_command(
    message: Message,
    state: FSMContext,
    telegram_service: FromDishka[TelegramService],
) -> None:
    await state.clear()
    await telegram_service.send_message(
        chat_id=message.chat.id,
        text="Админ-панель",
        reply_markup=admin_menu_keyboard(),
    )


@router.callback_query(
    AdminMenuCallback.filter(),
    GroupFilter(Group.ADMIN),
)
async def handle_admin_menu_callback(
    callback: CallbackQuery,
    callback_data: AdminMenuCallback,
    state: FSMContext,
    telegram_service: FromDishka[TelegramService],
) -> None:
    await callback.answer()
    chat_id = callback.message.chat.id if callback.message else callback.from_user.id
    if callback_data.action == "report":
        await state.set_state(AdminStates.waiting_report_tab_number)
        await telegram_service.send_message(
            chat_id=chat_id,
            text="Введите табельный номер сотрудника.",
            reply_markup=remove_keyboard(),
        )
    elif callback_data.action == "import":
        await state.set_state(AdminStates.waiting_import_file)
        await telegram_service.send_message(
            chat_id=chat_id,
            text=(
                "Пришлите XLSX-файл с сотрудниками. "
                "Первая строка должна содержать названия столбцов."
            ),
            reply_markup=remove_keyboard(),
        )
    else:
        await telegram_service.send_message(
            chat_id=chat_id,
            text="Неизвестное действие.",
            reply_markup=admin_menu_keyboard(),
        )


@router.message(
    AdminStates.waiting_report_tab_number,
    GroupFilter(Group.ADMIN),
    ChatTypeFilter(ChatType.PRIVATE),
)
async def admin_report_tab_number(
    message: Message,
    state: FSMContext,
    checklist_flow_service: FromDishka[ChecklistFlowService],
    telegram_service: FromDishka[TelegramService],
) -> None:
    tab_number = (message.text or "").strip()
    if not tab_number:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Табельный номер не распознан. Попробуйте ещё раз.",
        )
        return

    employee = await checklist_flow_service.get_employee_by_tab_number(tab_number)
    if employee is None:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Сотрудник с таким табельным номером не найден. Попробуйте снова.",
        )
        return

    if not employee.is_active:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Внимание: сотрудник помечен как неактивный, будет показан последний отчёт.",
        )

    await state.update_data(employee_id=employee.id, tab_number=tab_number)
    await state.set_state(AdminStates.waiting_report_date)
    await telegram_service.send_message(
        chat_id=message.chat.id,
        text="Введите дату отчёта в формате ДД.ММ.ГГГГ.",
    )


def _parse_report_date(raw: str) -> date | None:
    try:
        parsed = datetime.strptime(raw.strip(), "%d.%m.%Y")
    except ValueError:
        return None
    return parsed.date()


@router.message(
    AdminStates.waiting_report_date,
    GroupFilter(Group.ADMIN),
    ChatTypeFilter(ChatType.PRIVATE),
)
async def admin_report_date(
    message: Message,
    state: FSMContext,
    checklist_flow_service: FromDishka[ChecklistFlowService],
    telegram_service: FromDishka[TelegramService],
) -> None:
    report_raw = message.text or ""
    report_date = _parse_report_date(report_raw)
    if report_date is None:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Не удалось распознать дату. Используйте формат ДД.ММ.ГГГГ.",
        )
        return

    data = await state.get_data()
    employee_id = data.get("employee_id")
    if employee_id is None:
        await state.clear()
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Контекст отчёта потерян. Начните заново через /admin.",
        )
        return

    session = await checklist_flow_service.get_completed_session_for_employee_on_date(
        employee_id=employee_id,
        target_date=report_date,
    )
    if session is None:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Заполненный чеклист за эту дату не найден.",
            reply_markup=admin_menu_keyboard(),
        )
        await state.clear()
        return

    await _send_report(
        telegram_service=telegram_service,
        checklist_flow_service=checklist_flow_service,
        chat_id=message.chat.id,
        session_id=session.id,
        report_date=report_date,
    )
    await state.clear()


async def _send_report(
    telegram_service: TelegramService,
    checklist_flow_service: ChecklistFlowService,
    chat_id: int,
    session_id: int,
    report_date: date,
) -> None:
    session = await checklist_flow_service.load_session(session_id)
    if session is None:
        await telegram_service.send_message(
            chat_id=chat_id,
            text="Не удалось загрузить детали отчёта.",
        )
        return

    employee = session.employee
    checklist = session.checklist
    employee_status = " (неактивен)" if not employee.is_active else ""
    group_name = session.checklist.group.name if session.checklist.group else None
    header_lines = [
        "Отчёт по чеклисту",
        f"Сотрудник: табельный № {employee.tab_number}{employee_status}",
        f"Должность: {employee.position.name}" if employee.position else "",
        f"Группа: {group_name}" if group_name else "",
        f"Чеклист: {checklist.title}",
        f"Дата: {report_date.strftime('%d.%m.%Y')}",
    ]
    header = "\n".join(line for line in header_lines if line)
    await telegram_service.send_message(
        chat_id=chat_id,
        text=header,
    )

    questions = await checklist_flow_service.list_questions(checklist.id)
    answers_by_question = {answer.question_id: answer for answer in session.answers}
    for index, question in enumerate(questions, start=1):
        answer = answers_by_question.get(question.id)
        answer_label = (
            ANSWER_LABELS.get(answer.answer, answer.answer.value)
            if answer
            else "Нет ответа"
        )
        text = (
            f"{index}. {question.text}\n"
            f"Ответ: {answer_label}"
        )
        await telegram_service.send_message(
            chat_id=chat_id,
            text=text,
        )
        if answer and answer.photo_file_id:
            await telegram_service.bot.send_photo(
                chat_id=chat_id,
                photo=answer.photo_file_id,
                caption="Фото подтверждение",
            )

    if session.feedback_text:
        await telegram_service.send_message(
            chat_id=chat_id,
            text=f"Отзыв: {session.feedback_text}",
        )
    if session.feedback_voice_file_id:
        await telegram_service.bot.send_voice(
            chat_id=chat_id,
            voice=session.feedback_voice_file_id,
            caption="Голосовой отзыв",
        )

    await telegram_service.send_message(
        chat_id=chat_id,
        text="Готово.",
        reply_markup=admin_menu_keyboard(),
    )


@router.message(
    AdminStates.waiting_import_file,
    GroupFilter(Group.ADMIN),
    ChatTypeFilter(ChatType.PRIVATE),
    F.document,
)
async def handle_import_document(
    message: Message,
    state: FSMContext,
    telegram_service: FromDishka[TelegramService],
    employee_import_service: FromDishka[EmployeeImportService],
) -> None:
    document = message.document
    if document is None:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Не удалось получить файл. Попробуйте ещё раз.",
        )
        return

    if not (document.file_name or "").lower().endswith(".xlsx"):
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Поддерживаются только файлы в формате .xlsx. Пришлите корректный файл.",
        )
        return
    await telegram_service.send_message(
        chat_id=message.chat.id,
        text="Начинаю анализ...",
    )
    try:
        file = await telegram_service.bot.get_file(document.file_id)
        buffer = io.BytesIO()
        await telegram_service.bot.download(file, destination=buffer)
        stats = await employee_import_service.import_from_bytes(buffer.getvalue())
    except ValueError as exc:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text=f"Ошибка импорта: {exc}",
        )
        return
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to import employees", exc_info=exc)
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Произошла непредвиденная ошибка при импорте. Попробуйте позже.",
        )
        return

    await telegram_service.send_message(
        chat_id=message.chat.id,
        text="Импорт завершён.\n" + stats.as_message(),
    )
    await state.clear()
    await telegram_service.send_message(
        chat_id=message.chat.id,
        text="Админ-панель",
        reply_markup=admin_menu_keyboard(),
    )


@router.message(
    AdminStates.waiting_import_file,
    GroupFilter(Group.ADMIN),
    ChatTypeFilter(ChatType.PRIVATE),
)
async def handle_import_non_document(
    message: Message,
    telegram_service: FromDishka[TelegramService],
) -> None:
    await telegram_service.send_message(
        chat_id=message.chat.id,
        text="Пришлите файл .xlsx для импорта сотрудников.",
    )
