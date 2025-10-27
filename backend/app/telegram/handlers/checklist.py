from collections.abc import Mapping

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, PhotoSize
from dishka import FromDishka
from entities.checklist.enums import ChecklistAnswerValue
from entities.checklist.models import ChecklistQuestion, Employee
from entities.user.models import User
from services.checklist import ChecklistFlowService
from services.position_change import PositionChangeRequestService
from services.telegram import TelegramService
from shared.enums.group import Group
from telegram.callback_data.checklist import (
    FeedbackCallback,
    PositionConfirmCallback,
)
from telegram.keyboards.checklist import (
    checklist_answer_keyboard,
    feedback_choice_keyboard,
    position_confirmation_keyboard,
    remove_keyboard,
)
from telegram.middlewares.filters.chat import ChatTypeFilter
from telegram.middlewares.filters.permissions import GroupFilter
from telegram.states.checklist import ChecklistStates

router = Router()


ANSWER_BY_TEXT: Mapping[str, ChecklistAnswerValue] = {
    "да": ChecklistAnswerValue.YES,
    "нет": ChecklistAnswerValue.NO,
    "не применимо": ChecklistAnswerValue.NOT_APPLICABLE,
}


async def _present_question(
    telegram_service: TelegramService,
    message: Message,
    state: FSMContext,
    question: ChecklistQuestion,
    question_ids: list[int],
) -> None:
    question_index = question_ids.index(question.id) + 1
    total_questions = len(question_ids)
    text_parts = [
        f"Вопрос {question_index} из {total_questions}",
        question.text,
    ]
    if question.requires_photo:
        text_parts.append(
            "После ответа пришлите фото подтверждения одним сообщением.",
        )
    await state.update_data(current_question_id=question.id)
    await telegram_service.send_message(
        chat_id=message.chat.id,
        text="\n\n".join(text_parts),
        reply_markup=checklist_answer_keyboard(),
    )


async def _advance_flow(
    *,
    telegram_service: TelegramService,
    checklist_flow_service: ChecklistFlowService,
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    session_id = data.get("session_id")
    if session_id is None:
        await state.clear()
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Не удалось определить сессию опроса. Начните заново командой /start.",
        )
        return

    session = await checklist_flow_service.load_session(session_id)
    if session is None:
        await state.clear()
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Не удалось загрузить текущий опрос. Попробуйте начать сначала командой /start.",
        )
        return

    questions = await checklist_flow_service.list_questions(
        session.checklist_id,
    )
    if not questions:
        await checklist_flow_service.complete_session(session)
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="В опросе нет вопросов. Сообщите администратору.",
        )
        await state.clear()
        await state.set_state(ChecklistStates.waiting_tab_number)
        return

    question_ids: list[int] = data.get("question_ids", [])
    if not question_ids:
        question_ids = [question.id for question in questions]
        await state.update_data(question_ids=question_ids)

    next_question = await checklist_flow_service.get_next_unanswered_question(
        session.id,
        questions,
    )
    if next_question is None:
        await checklist_flow_service.complete_session(session)
        await state.set_state(ChecklistStates.waiting_feedback_choice)
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text=(
                "Спасибо! Все вопросы пройдены, ответы сохранены. "
                "Вы можете оставить отзыв о чеклисте или пропустить этот шаг."
            ),
            reply_markup=feedback_choice_keyboard(),
        )
        return

    await state.set_state(ChecklistStates.waiting_answer)
    await _present_question(
        telegram_service,
        message,
        state,
        next_question,
        question_ids,
    )


async def _start_checklist_flow(
    *,
    user: User,
    employee: Employee,
    state: FSMContext,
    checklist_flow_service: ChecklistFlowService,
    telegram_service: TelegramService,
    chat_id: int,
    message: Message | None,
) -> None:
    await state.update_data(
        pending_employee_tab=None,
        pending_employee_id=None,
    )

    checklist = await checklist_flow_service.get_active_checklist_for_employee(
        employee,
    )
    if checklist is None:
        await telegram_service.send_message(
            chat_id=chat_id,
            text=(
                "Подходящий чеклист не найден. Обратитесь к администратору, "
                "чтобы настроить вашу должность или группу."
            ),
        )
        await state.set_state(ChecklistStates.waiting_tab_number)
        return

    session, created = await checklist_flow_service.start_or_get_session(
        user_id=user.id,
        employee=employee,
        checklist=checklist,
    )
    session = await checklist_flow_service.load_session(session.id)
    if session is None:
        await telegram_service.send_message(
            chat_id=chat_id,
            text="Не удалось подготовить опрос. Попробуйте позже.",
        )
        await state.set_state(ChecklistStates.waiting_tab_number)
        return

    questions = await checklist_flow_service.list_questions(
        session.checklist_id,
    )
    if not questions:
        await checklist_flow_service.complete_session(session)
        await telegram_service.send_message(
            chat_id=chat_id,
            text="В опросе нет вопросов. Сообщите администратору.",
        )
        await state.set_state(ChecklistStates.waiting_tab_number)
        return

    await state.update_data(
        session_id=session.id,
        question_ids=[question.id for question in questions],
    )

    info_message = None
    if not created and session.employee_id != employee.id:
        info_message = await telegram_service.send_message(
            chat_id=chat_id,
            text="У вас уже есть незавершенный опрос. Продолжаем его.",
        )
    else:
        position_name = employee.position.name if employee.position else ""
        employee_label = f"Табельный № {employee.tab_number}"
        if position_name:
            employee_label = f"{employee_label} ({position_name})"
        info_message = await telegram_service.send_message(
            chat_id=chat_id,
            text=f"Найден сотрудник {employee_label}. Начинаем опрос.",
        )

    base_message = info_message or message
    if base_message is None:
        base_message = await telegram_service.send_message(
            chat_id=chat_id,
            text="Продолжаем опрос.",
        )
        if base_message is None:
            return

    await _advance_flow(
        telegram_service=telegram_service,
        checklist_flow_service=checklist_flow_service,
        message=base_message,
        state=state,
    )


async def _save_feedback_and_finish(
    *,
    message: Message,
    state: FSMContext,
    checklist_flow_service: ChecklistFlowService,
    telegram_service: TelegramService,
    feedback_text: str | None = None,
    feedback_voice_file_id: str | None = None,
    feedback_voice_unique_id: str | None = None,
) -> None:
    data = await state.get_data()
    session_id = data.get("session_id")
    if session_id is None:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Сессия не найдена. Начните заново командой /start.",
        )
        await state.clear()
        await state.set_state(ChecklistStates.waiting_tab_number)
        return
    session = await checklist_flow_service.load_session(session_id)
    if session is None:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Не удалось загрузить данные. Попробуйте позже.",
        )
        await state.clear()
        await state.set_state(ChecklistStates.waiting_tab_number)
        return
    await checklist_flow_service.save_feedback(
        session=session,
        feedback_text=feedback_text,
        feedback_voice_file_id=feedback_voice_file_id,
        feedback_voice_unique_id=feedback_voice_unique_id,
    )
    await telegram_service.send_message(
        chat_id=message.chat.id,
        text="Спасибо за отзыв!",
    )
    await _finish_session_flow(state, telegram_service, message.chat.id)


async def _finish_session_flow(
    state: FSMContext,
    telegram_service: TelegramService,
    chat_id: int,
) -> None:
    await telegram_service.send_message(
        chat_id=chat_id,
        text="Если нужно пройти еще один чеклист, отправьте новый табельный номер.",
        reply_markup=remove_keyboard(),
    )
    await state.clear()
    await state.set_state(ChecklistStates.waiting_tab_number)


@router.message(
    ChecklistStates.waiting_tab_number,
    GroupFilter(Group.USER),
    ChatTypeFilter(ChatType.PRIVATE),
)
async def handle_tab_number(
    message: Message,
    state: FSMContext,
    user: User,
    checklist_flow_service: FromDishka[ChecklistFlowService],
    telegram_service: FromDishka[TelegramService],
) -> None:
    tab_number = (message.text or "").strip()
    if not tab_number:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Введите, пожалуйста, табельный номер цифрами.",
        )
        return

    employee = await checklist_flow_service.get_employee_by_tab_number(
        tab_number,
    )
    if employee is None or not employee.is_active:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Сотрудник с таким табельным номером не найден или уже неактивен. Уточните номер и попробуйте снова.",
        )
        return

    position_name = (
        employee.position.name if employee.position else "не указана"
    )
    await state.update_data(
        pending_employee_tab=employee.tab_number,
        pending_employee_id=employee.id,
    )
    await state.set_state(ChecklistStates.confirm_position)
    await telegram_service.send_message(
        chat_id=message.chat.id,
        text=(f"Текущая должность: {position_name}.\nЭто ваша должность?"),
        reply_markup=position_confirmation_keyboard(),
    )


@router.callback_query(
    ChecklistStates.confirm_position,
    PositionConfirmCallback.filter(),
    GroupFilter(Group.USER),
)
async def handle_position_confirmation(
    callback: CallbackQuery,
    callback_data: PositionConfirmCallback,
    state: FSMContext,
    user: User,
    checklist_flow_service: FromDishka[ChecklistFlowService],
    telegram_service: FromDishka[TelegramService],
    position_change_service: FromDishka[PositionChangeRequestService],
) -> None:
    await callback.answer()
    data = await state.get_data()
    tab_number = data.get("pending_employee_tab")
    chat_id = (
        callback.message.chat.id if callback.message else callback.from_user.id
    )

    if tab_number is None:
        await state.set_state(ChecklistStates.waiting_tab_number)
        await telegram_service.send_message(
            chat_id=chat_id,
            text="Состояние утеряно. Введите табельный номер ещё раз.",
        )
        return

    action = callback_data.action
    if action == "deny":
        await state.set_state(ChecklistStates.waiting_tab_number)
        await telegram_service.send_message(
            chat_id=chat_id,
            text="Введите корректный табельный номер.",
            reply_markup=remove_keyboard(),
        )
        await state.update_data(
            pending_employee_tab=None,
            pending_employee_id=None,
        )
        return

    if action == "request_change":
        employee = await checklist_flow_service.get_employee_by_tab_number(
            tab_number,
        )
        if employee is None:
            await telegram_service.send_message(
                chat_id=chat_id,
                text="Не удалось найти сотрудника для заявки. Попробуйте позже.",
            )
            await state.set_state(ChecklistStates.waiting_tab_number)
            return
        success = await position_change_service.send_request(user, employee)
        if success:
            await telegram_service.send_message(
                chat_id=chat_id,
                text="Заявка успешно отправлена. Ожидайте обновления и повторите попытку позже.",
            )
        else:
            await telegram_service.send_message(
                chat_id=chat_id,
                text="Не удалось отправить заявку на смену должности. Сообщите администратору.",
            )
        await state.set_state(ChecklistStates.waiting_tab_number)
        return

    if action != "confirm":
        await telegram_service.send_message(
            chat_id=chat_id,
            text="Неизвестное действие. Введите табельный номер ещё раз.",
        )
        await state.set_state(ChecklistStates.waiting_tab_number)
        return

    employee = await checklist_flow_service.get_employee_by_tab_number(
        tab_number,
    )
    if employee is None or not employee.is_active:
        await telegram_service.send_message(
            chat_id=chat_id,
            text="Сотрудник не найден или стал неактивным. Введите табельный номер снова.",
        )
        await state.set_state(ChecklistStates.waiting_tab_number)
        return

    base_message = callback.message
    await _start_checklist_flow(
        user=user,
        employee=employee,
        state=state,
        checklist_flow_service=checklist_flow_service,
        telegram_service=telegram_service,
        chat_id=chat_id,
        message=base_message,
    )


@router.callback_query(
    ChecklistStates.waiting_feedback_choice,
    FeedbackCallback.filter(),
    GroupFilter(Group.USER),
)
async def handle_feedback_choice(
    callback: CallbackQuery,
    callback_data: FeedbackCallback,
    state: FSMContext,
    telegram_service: FromDishka[TelegramService],
) -> None:
    await callback.answer()
    chat_id = (
        callback.message.chat.id if callback.message else callback.from_user.id
    )
    action = callback_data.action
    if action == "provide":
        await state.set_state(ChecklistStates.waiting_feedback)
        await telegram_service.send_message(
            chat_id=chat_id,
            text="Расскажите, что можно улучшить. Можно отправить текст или голосовое сообщение.",
            reply_markup=remove_keyboard(),
        )
        return
    await telegram_service.send_message(
        chat_id=chat_id,
        text="Отзыв пропущен.",
    )
    await _finish_session_flow(state, telegram_service, chat_id)


@router.message(
    ChecklistStates.waiting_feedback,
    GroupFilter(Group.USER),
    ChatTypeFilter(ChatType.PRIVATE),
    F.text,
)
async def handle_feedback_text(
    message: Message,
    state: FSMContext,
    checklist_flow_service: FromDishka[ChecklistFlowService],
    telegram_service: FromDishka[TelegramService],
) -> None:
    await _save_feedback_and_finish(
        message=message,
        state=state,
        checklist_flow_service=checklist_flow_service,
        telegram_service=telegram_service,
        feedback_text=message.text,
    )


@router.message(
    ChecklistStates.waiting_feedback,
    GroupFilter(Group.USER),
    ChatTypeFilter(ChatType.PRIVATE),
    F.voice,
)
async def handle_feedback_voice(
    message: Message,
    state: FSMContext,
    checklist_flow_service: FromDishka[ChecklistFlowService],
    telegram_service: FromDishka[TelegramService],
) -> None:
    voice = message.voice
    if voice is None:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Не удалось обработать голосовое сообщение. Попробуйте снова.",
        )
        return
    await _save_feedback_and_finish(
        message=message,
        state=state,
        checklist_flow_service=checklist_flow_service,
        telegram_service=telegram_service,
        feedback_voice_file_id=voice.file_id,
        feedback_voice_unique_id=voice.file_unique_id,
    )


@router.message(
    ChecklistStates.waiting_feedback,
    GroupFilter(Group.USER),
    ChatTypeFilter(ChatType.PRIVATE),
)
async def handle_feedback_invalid(
    message: Message,
    telegram_service: FromDishka[TelegramService],
) -> None:
    await telegram_service.send_message(
        chat_id=message.chat.id,
        text="Пришлите текст или голосовое сообщение, либо нажмите 'Пропустить'.",
    )


@router.message(
    ChecklistStates.waiting_answer,
    GroupFilter(Group.USER),
    ChatTypeFilter(ChatType.PRIVATE),
    F.text,
)
async def handle_answer(
    message: Message,
    state: FSMContext,
    checklist_flow_service: FromDishka[ChecklistFlowService],
    telegram_service: FromDishka[TelegramService],
) -> None:
    normalized_answer = message.text.lower().strip()
    if normalized_answer not in ANSWER_BY_TEXT:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Используйте кнопки для ответа: Да, Нет или Не применимо.",
        )
        return

    data = await state.get_data()
    session_id = data.get("session_id")
    current_question_id = data.get("current_question_id")
    if session_id is None or current_question_id is None:
        await state.clear()
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Состояние опроса потеряно. Начните заново командой /start.",
        )
        return

    session = await checklist_flow_service.load_session(session_id)
    if session is None:
        await state.clear()
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Не удалось загрузить данные опроса. Попробуйте начать заново.",
        )
        return

    questions = await checklist_flow_service.list_questions(
        session.checklist_id,
    )
    question = next(
        (q for q in questions if q.id == current_question_id),
        None,
    )
    if question is None:
        await _advance_flow(
            telegram_service=telegram_service,
            checklist_flow_service=checklist_flow_service,
            message=message,
            state=state,
        )
        return

    answer_value = ANSWER_BY_TEXT[normalized_answer]
    await state.update_data(pending_answer_value=answer_value.value)

    if question.requires_photo:
        await state.set_state(ChecklistStates.waiting_photo)
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Пожалуйста, пришлите фото для подтверждения.",
            reply_markup=remove_keyboard(),
        )
        return

    await checklist_flow_service.save_answer(
        session=session,
        question=question,
        answer=answer_value,
    )

    await state.update_data(pending_answer_value=None)

    await _advance_flow(
        telegram_service=telegram_service,
        checklist_flow_service=checklist_flow_service,
        message=message,
        state=state,
    )


@router.message(
    ChecklistStates.waiting_answer,
    GroupFilter(Group.USER),
    ChatTypeFilter(ChatType.PRIVATE),
)
async def handle_non_text_answer(
    message: Message,
    telegram_service: FromDishka[TelegramService],
) -> None:
    await telegram_service.send_message(
        chat_id=message.chat.id,
        text="Ответ принимается только в виде текста. Выберите вариант с помощью кнопок.",
    )


@router.message(
    ChecklistStates.waiting_photo,
    GroupFilter(Group.USER),
    ChatTypeFilter(ChatType.PRIVATE),
    F.photo,
)
async def handle_photo(
    message: Message,
    state: FSMContext,
    checklist_flow_service: FromDishka[ChecklistFlowService],
    telegram_service: FromDishka[TelegramService],
) -> None:
    data = await state.get_data()
    session_id = data.get("session_id")
    current_question_id = data.get("current_question_id")
    pending_answer_value = data.get("pending_answer_value")
    if (
        session_id is None
        or current_question_id is None
        or pending_answer_value is None
    ):
        await state.clear()
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Не удалось определить, к какому вопросу относится фото. Начните заново командой /start.",
        )
        return

    session = await checklist_flow_service.load_session(session_id)
    if session is None:
        await state.clear()
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Не удалось загрузить данные опроса. Попробуйте начать заново.",
        )
        return

    questions = await checklist_flow_service.list_questions(
        session.checklist_id,
    )
    question = next(
        (q for q in questions if q.id == current_question_id),
        None,
    )
    if question is None:
        await _advance_flow(
            telegram_service=telegram_service,
            checklist_flow_service=checklist_flow_service,
            message=message,
            state=state,
        )
        return

    photo: PhotoSize = message.photo[-1]
    await checklist_flow_service.save_answer(
        session=session,
        question=question,
        answer=ChecklistAnswerValue(pending_answer_value),
        photo_file_id=photo.file_id,
        photo_unique_id=photo.file_unique_id,
    )

    await state.update_data(pending_answer_value=None)

    await _advance_flow(
        telegram_service=telegram_service,
        checklist_flow_service=checklist_flow_service,
        message=message,
        state=state,
    )


@router.message(
    ChecklistStates.waiting_photo,
    GroupFilter(Group.USER),
    ChatTypeFilter(ChatType.PRIVATE),
)
async def handle_non_photo_in_photo_state(
    message: Message,
    telegram_service: FromDishka[TelegramService],
) -> None:
    await telegram_service.send_message(
        chat_id=message.chat.id,
        text="Нужно отправить фотографию одним сообщением.",
    )
