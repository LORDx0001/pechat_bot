from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from bot.translations import _t

def get_language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")
    )
    return builder.as_markup()

def get_main_menu_keyboard(language: str = "ru", is_manager: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=_t(language, "main_menu_order")),
        KeyboardButton(text=_t(language, "main_menu_catalog"))
    )
    builder.row(
        KeyboardButton(text=_t(language, "main_menu_cart")),
        KeyboardButton(text=_t(language, "main_menu_orders"))
    )
    
    if is_manager:
        builder.row(
            KeyboardButton(text=_t(language, "main_menu_support")),
            KeyboardButton(text=_t(language, "other_services")),
            KeyboardButton(text=_t(language, "main_menu_admin"))
        )
    else:
        builder.row(
            KeyboardButton(text=_t(language, "main_menu_support")),
            KeyboardButton(text=_t(language, "other_services"))
        )
    return builder.as_markup(resize_keyboard=True)

def get_manager_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📋 Новые заказы"),
        KeyboardButton(text="📦 В работе")
    )
    builder.row(
        KeyboardButton(text="📊 Статистика"),
        KeyboardButton(text="👤 Режим клиента")
    )
    return builder.as_markup(resize_keyboard=True)

def get_cancel_keyboard(language: str = "ru", cancel_text: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    text = cancel_text or _t(language, "cancel")
    builder.button(text=text, callback_data="cancel_action")
    return builder.as_markup()

def get_share_phone_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=_t(language, "share_phone"), request_contact=True)
    )
    builder.row(
        KeyboardButton(text=_t(language, "cancel_checkout"))
    )
    return builder.as_markup(resize_keyboard=True)

def get_categories_keyboard(categories: list, language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category["name"], callback_data=f"cat_{category['id']}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action"))
    return builder.as_markup()

def get_products_keyboard(products: list, category_id: int, language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for prod in products:
        price_text = f"{prod['title']} - {prod['price']} руб" if language == "ru" else f"{prod['title']} - {prod['price']} so'm"
        builder.button(text=price_text, callback_data=f"prod_{prod['id']}")
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text=_t(language, "back_to_categories"), callback_data="back_to_categories"),
        InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action")
    )
    return builder.as_markup()

def get_sizes_keyboard(sizes: list, language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in sizes:
        builder.button(text=s["name"], callback_data=f"size_{s['id']}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action"))
    return builder.as_markup()

def get_colors_keyboard(colors: list, language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in colors:
        builder.button(text=c["name"], callback_data=f"color_{c['id']}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action"))
    return builder.as_markup()

def get_print_positions_keyboard(positions: list, language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pos in positions:
        text = f"{pos['name']} (+{pos['extra_price']} руб)" if language == "ru" else f"{pos['name']} (+{pos['extra_price']} so'm)"
        builder.button(text=text, callback_data=f"print_{pos['id']}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action"))
    return builder.as_markup()

def get_comment_skip_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(language, "skip"), callback_data="skip_comment")
    builder.row(InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action"))
    return builder.as_markup()

def get_cart_keyboard(cart_items: list, language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for item in cart_items:
        prod_title = item['product_details']['title']
        builder.row(
            InlineKeyboardButton(text=f"➖ {prod_title}", callback_data=f"cart_qty_dec_{item['id']}"),
            InlineKeyboardButton(text=f"➕ {prod_title}", callback_data=f"cart_qty_inc_{item['id']}"),
            InlineKeyboardButton(text="🗑️", callback_data=f"cart_del_{item['id']}")
        )
    
    builder.row(
        InlineKeyboardButton(text="🗑️ " + _t(language, "empty_cart"), callback_data="cart_clear"),
        InlineKeyboardButton(text=_t(language, "checkout"), callback_data="cart_checkout")
    )
    return builder.as_markup()

def get_checkout_confirm_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(language, "confirm_checkout"), callback_data="checkout_confirm")
    builder.row(InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action"))
    return builder.as_markup()

def get_pay_payment_keyboard(order_id: int, language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(language, "i_paid"), callback_data=f"pay_paid_{order_id}")
    return builder.as_markup()

def get_design_2_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(language, "use_same_design"), callback_data="skip_design_2")
    builder.row(InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action"))
    return builder.as_markup()
