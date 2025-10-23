from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    waiting_report_tab_number = State()
    waiting_report_date = State()
    waiting_import_file = State()
