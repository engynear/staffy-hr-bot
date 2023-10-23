from aiogram.fsm.state import State, StatesGroup

class UserInfo(StatesGroup):
    GetName = State()

class TeamStatus(StatesGroup):
    NotInTeam = State()
    InTeam = State()

class WishFSM(StatesGroup):
    SelectTeamMember = State()     # Выбор члена команды
    WriteWish = State()            # Написание пожелания
    WaitingForContinue = State()   # Ожидание продолжения