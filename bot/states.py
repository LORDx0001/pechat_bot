from aiogram.fsm.state import State, StatesGroup

class OrderingStates(StatesGroup):
    category = State()
    product = State()
    size = State()
    color = State()
    print_position = State()
    design_file = State()
    design_file_2 = State()
    comment = State()
    quantity = State()

class CheckoutStates(StatesGroup):
    full_name = State()
    phone = State()
    city = State()
    address = State()

class ReceiptStates(StatesGroup):
    waiting_for_receipt = State()  # holds state when uploading payment receipts

class SupportStates(StatesGroup):
    waiting_for_message = State()  # holds state when user chats with support/manager

class OtherServicesStates(StatesGroup):
    comment = State()
    phone = State()
