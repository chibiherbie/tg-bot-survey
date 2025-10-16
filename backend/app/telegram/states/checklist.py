from aiogram.fsm.state import State, StatesGroup


class ChecklistStates(StatesGroup):
    waiting_tab_number = State()
    waiting_answer = State()
    waiting_photo = State()
