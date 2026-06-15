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
        KeyboardButton(text="📥 Заявки на подтверждение")
    )
    builder.row(
        KeyboardButton(text="📦 В работе"),
        KeyboardButton(text="📊 Статистика")
    )
    builder.row(
        KeyboardButton(text="👤 Режим клиента")
    )
    return builder.as_markup(resize_keyboard=True)

def get_cancel_keyboard(language: str = "ru", cancel_text: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    text = cancel_text or _t(language, "cancel")
    builder.button(text=text, callback_data="cancel_action")
    return builder.as_markup()

def get_back_cancel_keyboard(language: str = "ru", back_callback_data: str = "back_action", cancel_text: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=_t(language, "back"), callback_data=back_callback_data),
        InlineKeyboardButton(text=cancel_text or _t(language, "cancel"), callback_data="cancel_action")
    )
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
        name = category.get("name_uz") if (language == "uz" and category.get("name_uz")) else category["name"]
        builder.button(text=name, callback_data=f"cat_{category['id']}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action"))
    return builder.as_markup()

def get_products_keyboard(products: list, category_id: int, language: str = "ru", currency: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not currency:
        currency = "сум" if language == "ru" else "so'm"
    for prod in products:
        title = prod.get("title_uz") if (language == "uz" and prod.get("title_uz")) else prod["title"]
        price_text = f"{title} - {prod['price']} {currency}"
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
    builder.row(
        InlineKeyboardButton(text=_t(language, "back"), callback_data="back_to_products"),
        InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action")
    )
    return builder.as_markup()

def get_colors_keyboard(colors: list, language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in colors:
        name = c.get("name_uz") if (language == "uz" and c.get("name_uz")) else c["name"]
        builder.button(text=name, callback_data=f"color_{c['id']}")
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text=_t(language, "back"), callback_data="back_to_sizes"),
        InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action")
    )
    return builder.as_markup()

def get_print_positions_keyboard(positions: list, language: str = "ru", currency: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not currency:
        currency = "сум" if language == "ru" else "so'm"
    for pos in positions:
        name = pos.get("name_uz") if (language == "uz" and pos.get("name_uz")) else pos["name"]
        text = f"{name} (+{pos['extra_price']} {currency})"
        builder.button(text=text, callback_data=f"print_{pos['id']}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action"))
    return builder.as_markup()

def get_comment_skip_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_t(language, "skip"), callback_data="skip_comment")
    builder.row(
        InlineKeyboardButton(text=_t(language, "back"), callback_data="back_to_designs"),
        InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action")
    )
    return builder.as_markup()

def get_cart_keyboard(cart_items: list, language: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for item in cart_items:
        prod_details = item['product_details']
        prod_title = prod_details.get("title_uz") if (language == "uz" and prod_details.get("title_uz")) else prod_details['title']
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
    builder.row(
        InlineKeyboardButton(text=_t(language, "back"), callback_data="back_to_design1"),
        InlineKeyboardButton(text=_t(language, "cancel"), callback_data="cancel_action")
    )
    return builder.as_markup()

def get_categories_reply_keyboard(categories: list, language: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for category in categories:
        name = category.get("name_uz") if (language == "uz" and category.get("name_uz")) else category["name"]
        builder.button(text=name)
    builder.adjust(2)
    builder.row(KeyboardButton(text=_t(language, "cancel")))
    return builder.as_markup(resize_keyboard=True)

def get_products_reply_keyboard(products: list, language: str = "ru", currency: str = None) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    if not currency:
        currency = "so'm" if language == "uz" else "сум"
    for prod in products:
        title = prod.get("title_uz") if (language == "uz" and prod.get("title_uz")) else prod["title"]
        price_text = f"{title} - {prod['price']} {currency}"
        builder.button(text=price_text)
    builder.adjust(1)
    builder.row(
        KeyboardButton(text=_t(language, "back")),
        KeyboardButton(text=_t(language, "cancel"))
    )
    return builder.as_markup(resize_keyboard=True)

def get_sizes_reply_keyboard(sizes: list, language: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for s in sizes:
        builder.button(text=s["name"])
    builder.adjust(3)
    builder.row(
        KeyboardButton(text=_t(language, "back")),
        KeyboardButton(text=_t(language, "cancel"))
    )
    return builder.as_markup(resize_keyboard=True)

def get_colors_reply_keyboard(colors: list, language: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for c in colors:
        name = c.get("name_uz") if (language == "uz" and c.get("name_uz")) else c["name"]
        builder.button(text=name)
    builder.adjust(2)
    builder.row(
        KeyboardButton(text=_t(language, "back")),
        KeyboardButton(text=_t(language, "cancel"))
    )
    return builder.as_markup(resize_keyboard=True)

def get_print_positions_reply_keyboard(positions: list, language: str = "ru", currency: str = None) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    if not currency:
        currency = "so'm" if language == "uz" else "сум"
    for pos in positions:
        name = pos.get("name_uz") if (language == "uz" and pos.get("name_uz")) else pos["name"]
        text = f"{name} (+{pos['extra_price']} {currency})"
        builder.button(text=text)
    builder.adjust(1)
    builder.row(
        KeyboardButton(text=_t(language, "back")),
        KeyboardButton(text=_t(language, "cancel"))
    )
    return builder.as_markup(resize_keyboard=True)

def get_print_positions_carousel_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    
    confirm_text = "✅ Подтвердить" if language == "ru" else "✅ Tasdiqlash"
    prev_text = "⬅️ Пред." if language == "ru" else "⬅️ Oldingi"
    next_text = "➡️ След." if language == "ru" else "➡️ Keyingi"
    back_text = "Назад" if language == "ru" else "Orqaga"
    cancel_text = "Отменить" if language == "ru" else "Bekor qilish"
    
    builder.row(KeyboardButton(text=confirm_text))
    builder.row(
        KeyboardButton(text=prev_text),
        KeyboardButton(text=next_text)
    )
    builder.row(
        KeyboardButton(text=back_text),
        KeyboardButton(text=cancel_text)
    )
    return builder.as_markup(resize_keyboard=True)

def get_design_file_reply_keyboard(language: str = "ru", is_second: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    if is_second:
        builder.button(text=_t(language, "use_same_design"))
    builder.row(
        KeyboardButton(text=_t(language, "back")),
        KeyboardButton(text=_t(language, "cancel"))
    )
    return builder.as_markup(resize_keyboard=True)

def get_comment_reply_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=_t(language, "skip"))
    builder.row(
        KeyboardButton(text=_t(language, "back")),
        KeyboardButton(text=_t(language, "cancel"))
    )
    return builder.as_markup(resize_keyboard=True)

def get_quantity_reply_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for q in ["1", "2", "3", "5", "10"]:
        builder.button(text=q)
    builder.adjust(5)
    builder.row(
        KeyboardButton(text=_t(language, "back")),
        KeyboardButton(text=_t(language, "cancel"))
    )
    return builder.as_markup(resize_keyboard=True)
