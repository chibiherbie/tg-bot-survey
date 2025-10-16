from collections.abc import Mapping

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, PhotoSize
from dishka import FromDishka

from entities.checklist.enums import ChecklistAnswerValue
from entities.checklist.models import ChecklistQuestion
from entities.user.models import User
from services.checklist import ChecklistFlowService
from services.telegram import TelegramService
from shared.enums.group import Group
from telegram.keyboards.checklist import (
    checklist_answer_keyboard,
    remove_keyboard,
)
from telegram.middlewares.filters.chat import ChatTypeFilter
from telegram.middlewares.filters.permissions import GroupFilter
from telegram.states.checklist import ChecklistStates


router = Router()


ANSWER_BY_TEXT: Mapping[str, ChecklistAnswerValue] = {
    "да": ChecklistAnswerValue.YES,
    "нет": ChecklistAnswerValue.NO,
    "нельзя выполнить": ChecklistAnswerValue.NOT_APPLICABLE,
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
    text_parts = [f"Вопрос {question_index} из {total_questions}", question.text]
    if question.requires_photo:
        text_parts.append("После ответа пришлите фото подтверждения одним сообщением.")
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

    questions = await checklist_flow_service.list_questions(session.checklist_id)
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
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text=(
                "Спасибо! Все вопросы пройдены, ответы сохранены. "
                "Если нужно пройти еще один чеклист, отправьте новый табельный номер."
            ),
            reply_markup=remove_keyboard(),
        )
        await state.clear()
        await state.set_state(ChecklistStates.waiting_tab_number)
        return

    await state.set_state(ChecklistStates.waiting_answer)
    await _present_question(
        telegram_service,
        message,
        state,
        next_question,
        question_ids,
    )


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

    employee = await checklist_flow_service.get_employee_by_tab_number(tab_number)
    if employee is None:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Сотрудник с таким табельным номером не найден. Проверьте номер и попробуйте снова.",
        )
        return

    checklist = await checklist_flow_service.get_active_checklist_for_employee(
        employee,
    )
    if checklist is None:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Для вашей должности пока нет доступного опроса.",
        )
        await state.clear()
        return

    session, created = await checklist_flow_service.start_or_get_session(
        user_id=user.id,
        employee=employee,
        checklist=checklist,
    )
    session = await checklist_flow_service.load_session(session.id)
    if session is None:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="Не удалось подготовить опрос. Попробуйте позже.",
        )
        await state.clear()
        return

    questions = await checklist_flow_service.list_questions(session.checklist_id)
    if not questions:
        await checklist_flow_service.complete_session(session)
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="В опросе нет вопросов. Сообщите администратору.",
        )
        await state.clear()
        return

    await state.update_data(
        session_id=session.id,
        question_ids=[question.id for question in questions],
    )

    if not created and session.employee_id != employee.id:
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text="У вас уже есть незавершенный опрос. Продолжаем его.",
        )
    else:
        full_name = employee.full_name or "Сотрудник"
        position_name = employee.position.name if employee.position else ""
        await telegram_service.send_message(
            chat_id=message.chat.id,
            text=f"Начинаем опрос.",
        )

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
            text="Используйте кнопки для ответа: Да, Нет или Нельзя выполнить.",
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

    questions = await checklist_flow_service.list_questions(session.checklist_id)
    question = next((q for q in questions if q.id == current_question_id), None)
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
    if session_id is None or current_question_id is None or pending_answer_value is None:
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

    questions = await checklist_flow_service.list_questions(session.checklist_id)
    question = next((q for q in questions if q.id == current_question_id), None)
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
