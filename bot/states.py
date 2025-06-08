from aiogram.fsm.state import State, StatesGroup



class DepositStates(StatesGroup):
    waiting_for_account = State()
    waiting_for_amount = State()
    waiting_for_bank_choice = State()
    waiting_for_receipt = State()   


class WithdrawStates(StatesGroup):
    waiting_for_account = State()
    waiting_for_amount = State()
    waiting_for_bank = State()       
    waiting_for_phone = State()
    waiting_for_requisites = State()
    waiting_for_code = State()

class SetBankState(StatesGroup):
    name = State()
    
class AuthStates(StatesGroup):
    wait_for_password = State()

class SetPaymentMethodState(StatesGroup):
    choosing_bank = State()
    title = State()
    type = State()
    account_number = State()
    phone_number = State()
    holder_name = State()
    qr_photo = State()