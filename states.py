"""FSM states for private message handlers."""

from aiogram.fsm.state import State, StatesGroup


class FilterStates(StatesGroup):
    waiting_for_keyword = State()
