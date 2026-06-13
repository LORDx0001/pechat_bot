import logging
import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, BufferedInputFile, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api_client import api_client
from bot.keyboards import (
    get_main_menu_keyboard, get_cancel_keyboard, get_share_phone_keyboard,
    get_categories_keyboard, get_products_keyboard, get_sizes_keyboard,
    get_colors_keyboard, get_print_positions_keyboard, get_comment_skip_keyboard,
    get_cart_keyboard, get_checkout_confirm_keyboard, get_pay_payment_keyboard,
    get_manager_menu_keyboard, get_design_2_keyboard, get_language_keyboard
)
from bot.translations import _t
from bot.states import OrderingStates, CheckoutStates, ReceiptStates, SupportStates, OtherServicesStates

from bot.config import settings

logger = logging.getLogger(__name__)
router = Router()

async def get_user_lang_and_manager(user_id: int, username: str, first_name: str):
    client_info = await api_client.register_client(
        telegram_id=user_id,
        username=username or "",
        first_name=first_name or "Клиент"
    )
    user_lang = "ru"
    is_manager = False
    if client_info and not client_info.get("error"):
        user_lang = client_info.get("language") or "ru"
        is_manager = client_info.get("is_manager", False)
    return user_lang, is_manager

async def get_user_main_menu(telegram_id: int, username: str = "", first_name: str = ""):
    user_lang, is_manager = await get_user_lang_and_manager(telegram_id, username, first_name)
    return get_main_menu_keyboard(language=user_lang, is_manager=is_manager)


# =====================================================================
# GENERAL & MAIN MENU HANDLERS
# =====================================================================

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=get_language_keyboard())

@router.callback_query(F.data.startswith("lang_"))
async def select_language_callback(callback: CallbackQuery, state: FSMContext):
    lang_code = callback.data.split("_")[1] # "ru" or "uz"
    
    # Save/update language preference on backend
    client_info = await api_client.register_client(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        language=lang_code
    )
    
    is_manager = False
    if client_info and not client_info.get("error"):
        is_manager = client_info.get("is_manager", False)
        
    welcome_text = _t(lang_code, "welcome")
    
    await callback.message.delete()
    await callback.message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(language=lang_code, is_manager=is_manager)
    )
    await callback.answer()

@router.message(F.text == "Главное меню")
async def cmd_main_menu_text(message: Message, state: FSMContext):
    await state.clear()
    user_lang, is_manager = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    welcome_text = _t(user_lang, "welcome")
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(language=user_lang, is_manager=is_manager))

@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    order_id = data.get("order_id")
    
    user_lang, is_manager = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    
    restored = False
    if current_state == ReceiptStates.waiting_for_receipt.state and order_id:
        res = await api_client.cancel_order(order_id)
        if res and not res.get("error"):
            restored = True
            
    await state.clear()
    await callback.message.delete()
    
    if restored:
        alert_text = "Заказ отменен, товары возвращены в корзину." if user_lang == "ru" else "Buyurtma bekor qilindi, mahsulotlar savatchaga qaytarildi."
        msg_text = "Вы отменили оплату. Товары возвращены в корзину." if user_lang == "ru" else "To'lov bekor qilindi. Mahsulotlar savatchaga qaytarildi."
        await callback.answer(alert_text, show_alert=True)
        await callback.message.answer(
            msg_text,
            reply_markup=await get_user_main_menu(
                callback.from_user.id,
                callback.from_user.username,
                callback.from_user.first_name
            )
        )
    else:
        await callback.answer(_t(user_lang, "action_cancelled"))
        await callback.message.answer(
            _t(user_lang, "back_to_menu"), 
            reply_markup=await get_user_main_menu(
                callback.from_user.id, 
                callback.from_user.username, 
                callback.from_user.first_name
            )
        )

# =====================================================================
# SUPPORT FLOW
# =====================================================================

@router.message(F.text.in_({"💬 Поддержка", "💬 Yordam / Aloqa"}))
async def show_support(message: Message):
    user_lang, is_manager = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    store_settings = await api_client.get_settings()
    about_text = "Служба поддержки" if user_lang == "ru" else "Qo'llab-quvvatlash xizmati"
    if store_settings and not store_settings.get("error"):
        about_text = (store_settings.get("about_text_uz") if (user_lang == "uz" and store_settings.get("about_text_uz")) else store_settings.get("about_text")) or about_text
        
    manager_tg = store_settings.get("manager_telegram") or ""
    
    msg = f"ℹ️ <b>О компании / Kompaniya haqida:</b>\n{about_text}\n\n"
    if manager_tg:
        if user_lang == "ru":
            msg += f"💬 Для связи с менеджером: {manager_tg}\n\n"
        else:
            msg += f"💬 Menejer bilan bog'lanish: {manager_tg}\n\n"
            
    if user_lang == "ru":
        msg += "Вы также можете отправить сообщение прямо сюда, и менеджер ответит вам!"
    else:
        msg += "Shuningdek, xabaringizni to'g'ridan-to'g'ri shu yerga yuborishingiz mumkin, menejer javob beradi!"
        
    await message.answer(msg, parse_mode="HTML")

# =====================================================================
# CATALOG & ORDERING FLOW (FSM)
# =====================================================================

@router.message(F.text.in_({"🛍 Сделать заказ", "🛍 Buyurtma berish", "📂 Каталог", "📂 Katalog"}))
async def start_catalog(message: Message, state: FSMContext):
    await state.clear()
    user_lang, is_manager = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    categories = await api_client.get_categories()
    
    if not categories or (isinstance(categories, dict) and categories.get("error")):
        err_msg = "Ошибка загрузки категорий. Попробуйте позже." if user_lang == "ru" else "Kategoriyalarni yuklashda xatolik yuz berdi. Keyinroq urinib ko'ring."
        await message.answer(err_msg)
        return
        
    if not categories:
        empty_msg = "В каталоге пока нет доступных категорий." if user_lang == "ru" else "Katalogda hozircha mavjud kategoriyalar yo'q."
        await message.answer(empty_msg)
        return

    await state.set_state(OrderingStates.category)
    await message.answer(_t(user_lang, "choose_category"), reply_markup=get_categories_keyboard(categories, language=user_lang))

@router.callback_query(F.data.startswith("cat_"))
async def select_category(callback: CallbackQuery, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    category_id = int(callback.data.split("_")[1])
    products = await api_client.get_products(category_id)
    
    if not products or (isinstance(products, dict) and products.get("error")):
        err_msg = "Ошибка загрузки товаров." if user_lang == "ru" else "Mahsulotlarni yuklashda xatolik."
        await callback.answer(err_msg)
        return
        
    if not products:
        empty_msg = "В этой категории пока нет товаров." if user_lang == "ru" else "Ushbu kategoriyada hozircha mahsulotlar yo'q."
        await callback.answer(empty_msg)
        return
        
    await state.update_data(category_id=category_id)
    await state.set_state(OrderingStates.product)
    
    await callback.message.edit_text(
        _t(user_lang, "choose_product"), 
        reply_markup=get_products_keyboard(products, category_id, language=user_lang)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    categories = await api_client.get_categories()
    await state.set_state(OrderingStates.category)
    await callback.message.edit_text(_t(user_lang, "choose_category"), reply_markup=get_categories_keyboard(categories, language=user_lang))
    await callback.answer()

@router.callback_query(F.data.startswith("prod_"))
async def select_product(callback: CallbackQuery, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    product_id = int(callback.data.split("_")[1])
    product = await api_client.get_product_detail(product_id)
    
    if not product or product.get("error"):
        err_msg = "Ошибка загрузки деталей товара." if user_lang == "ru" else "Mahsulot tafsilotlarini yuklashda xatolik."
        await callback.answer(err_msg)
        return
        
    await state.update_data(product_id=product_id, product_data=product)
    
    sizes = product.get("sizes", [])
    if not sizes:
        await state.update_data(size_id=None)
        await proceed_to_colors(callback, state, product)
        return
        
    await state.set_state(OrderingStates.size)
    await callback.message.delete()
    title = product.get("title_uz") if (user_lang == "uz" and product.get("title_uz")) else product["title"]
    description = product.get("description_uz") if (user_lang == "uz" and product.get("description_uz")) else product["description"]
    if user_lang == "ru":
        caption = f"👕 <b>{title}</b>\n\n{description}\n\n💵 Цена: {product['price']} руб."
    else:
        caption = f"👕 <b>{title}</b>\n\n{description}\n\n💵 Narxi: {product['price']} so'm"
    if product.get("image"):
        async with aiohttp.ClientSession() as session:
            async with session.get(product["image"]) as resp:
                if resp.status == 200:
                    img_bytes = await resp.read()
                    await callback.message.answer_photo(
                        BufferedInputFile(img_bytes, filename="product.jpg"),
                        caption=caption,
                        parse_mode="HTML"
                    )
                else:
                    await callback.message.answer(caption, parse_mode="HTML")
    else:
        await callback.message.answer(caption, parse_mode="HTML")
        
    await callback.message.answer(_t(user_lang, "choose_size"), reply_markup=get_sizes_keyboard(sizes, language=user_lang))
    await callback.answer()

async def proceed_to_colors(callback: CallbackQuery, state: FSMContext, product: dict):
    user_lang, _ = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    colors = product.get("colors", [])
    if not colors:
        await state.update_data(color_id=None)
        await proceed_to_print_positions(callback, state)
        return
        
    await state.set_state(OrderingStates.color)
    await callback.message.answer(_t(user_lang, "choose_color"), reply_markup=get_colors_keyboard(colors, language=user_lang))

@router.callback_query(F.data.startswith("size_"))
async def select_size(callback: CallbackQuery, state: FSMContext):
    size_id = int(callback.data.split("_")[1])
    await state.update_data(size_id=size_id)
    
    data = await state.get_data()
    product = data["product_data"]
    
    await callback.message.delete()
    await proceed_to_colors(callback, state, product)
    await callback.answer()

async def proceed_to_print_positions(callback: CallbackQuery, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    positions = await api_client.get_print_positions()
    if not positions or (isinstance(positions, dict) and positions.get("error")):
        err_msg = "Ошибка загрузки мест нанесения принта. Отмена." if user_lang == "ru" else "Rasm bosish joylarini yuklashda xatolik. Bekor qilindi."
        await callback.message.answer(err_msg)
        await state.clear()
        return
        
    await state.set_state(OrderingStates.print_position)
    await state.update_data(print_positions_list=positions, current_print_index=0)
    
    await show_print_position_carousel(callback.message, positions, 0)

async def show_print_position_carousel(message: Message, positions: list, index: int, edit_media: bool = False):
    user_lang, _ = await get_user_lang_and_manager(
        message.chat.id,
        message.chat.username or "",
        message.chat.first_name or ""
    )
    pos = positions[index]
    if user_lang == "ru":
        caption = (
            f"📍 <b>Место нанесения принта ({index + 1}/{len(positions)}):</b>\n\n"
            f"<b>Название:</b> {pos['name']}\n"
            f"💵 <b>Наценка:</b> {pos['extra_price']} руб.\n\n"
            f"Выберите место нанесения, перелистывая варианты:"
        )
        prev_text = "◀️ Предыдущий"
        next_text = "Следующий ▶️"
        select_text = f"✅ Выбрать {pos['name']}"
        cancel_text = "❌ Отмена"
    else:
        caption = (
            f"📍 <b>Rasm bosiladigan joy ({index + 1}/{len(positions)}):</b>\n\n"
            f"<b>Nomi:</b> {pos['name']}\n"
            f"💵 <b>Ustama narxi:</b> {pos['extra_price']} so'm\n\n"
            f"Variantlarni ko'rib chiqib tanlang:"
        )
        prev_text = "◀️ Oldingi"
        next_text = "Keyingi ▶️"
        select_text = f"✅ Tanlash {pos['name']}"
        cancel_text = "❌ Bekor qilish"
        
    builder = InlineKeyboardBuilder()
    
    nav_buttons = []
    if len(positions) > 1:
        nav_buttons.append(InlineKeyboardButton(text=prev_text, callback_data="print_carousel_prev"))
        nav_buttons.append(InlineKeyboardButton(text=next_text, callback_data="print_carousel_next"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
        
    builder.row(InlineKeyboardButton(text=select_text, callback_data=f"print_carousel_select_{pos['id']}"))
    builder.row(InlineKeyboardButton(text=cancel_text, callback_data="cancel_action"))
    
    reply_markup = builder.as_markup()
    image_url = pos.get("image")
    
    img_bytes = None
    if image_url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        img_bytes = await resp.read()
        except Exception as e:
            logger.error(f"Failed to download carousel image: {e}")

    if img_bytes:
        photo_file = BufferedInputFile(img_bytes, filename="print_pos.png")
        if edit_media and message.photo:
            from aiogram.types import InputMediaPhoto
            await message.edit_media(
                media=InputMediaPhoto(media=photo_file, caption=caption, parse_mode="HTML"),
                reply_markup=reply_markup
            )
        else:
            try:
                await message.delete()
            except Exception:
                pass
            await message.answer_photo(
                photo=photo_file,
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
    else:
        if edit_media and not message.photo:
            await message.edit_text(text=caption, parse_mode="HTML", reply_markup=reply_markup)
        else:
            try:
                await message.delete()
            except Exception:
                pass
            await message.answer(text=caption, parse_mode="HTML", reply_markup=reply_markup)

@router.callback_query(F.data.startswith("color_"))
async def select_color(callback: CallbackQuery, state: FSMContext):
    color_id = int(callback.data.split("_")[1])
    await state.update_data(color_id=color_id)
    
    await callback.message.delete()
    await proceed_to_print_positions(callback, state)
    await callback.answer()

@router.callback_query(F.data.in_(["print_carousel_prev", "print_carousel_next"]))
async def print_carousel_navigation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    positions = data.get("print_positions_list")
    index = data.get("current_print_index", 0)
    
    if not positions:
        await callback.answer("Ошибка данных.")
        return
        
    if callback.data == "print_carousel_prev":
        index = (index - 1) % len(positions)
    else:
        index = (index + 1) % len(positions)
        
    await state.update_data(current_print_index=index)
    await show_print_position_carousel(callback.message, positions, index, edit_media=True)
    await callback.answer()

@router.callback_query(F.data.startswith("print_carousel_select_"))
async def select_print_carousel_position(callback: CallbackQuery, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    print_position_id = int(callback.data.split("_")[3])
    
    data = await state.get_data()
    positions = data.get("print_positions_list")
    pos = next((p for p in positions if p["id"] == print_position_id), None)
    
    if not pos:
        err_msg = "Ошибка выбора места нанесения." if user_lang == "ru" else "Rasm joyini tanlashda xatolik."
        await callback.answer(err_msg)
        return
        
    await state.update_data(print_position_id=print_position_id, print_position_data=pos)
    await callback.message.delete()
    
    requires_multiple = pos.get("requires_multiple_designs", False)
    if user_lang == "ru":
        prompt_text = (
            "Загрузите ваш макет/изображение для принта (<b>Макет 1 / Спереди</b>):\n\n" if requires_multiple else
            "Загрузите ваш макет/изображение для принта:\n\n"
        )
        prompt_text += (
            "Поддерживаемые форматы: JPG, PNG, PDF, SVG.\n"
            "Пожалуйста, отправьте файл как <b>Документ</b> (без сжатия) или как фото."
        )
    else:
        prompt_text = (
            "Rasm faylini yuklang (<b>1-rasm / Old tomoni</b>):\n\n" if requires_multiple else
            "Rasm faylini yuklang:\n\n"
        )
        prompt_text += (
            "Qo'llab-quvvatlanadigan formatlar: JPG, PNG, PDF, SVG.\n"
            "Iltimos, faylni <b>Hujjat</b> ko'rinishida (siquvsiz) yoki rasm sifatida yuboring."
        )
    
    await state.set_state(OrderingStates.design_file)
    await callback.message.answer(
        prompt_text,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(language=user_lang)
    )
    await callback.answer()

@router.message(OrderingStates.design_file, F.photo | F.document)
async def process_design_file(message: Message, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    file_id = None
    filename = "design.png"
    
    if message.document:
        file_id = message.document.file_id
        filename = message.document.file_name
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in ["jpg", "jpeg", "png", "pdf", "svg"]:
            err_msg = "Неподдерживаемый формат файла. Загрузите JPG, PNG, PDF или SVG." if user_lang == "ru" else "Qo'llab-quvvatlanmaydigan format. JPG, PNG, PDF yoki SVG yuklang."
            await message.answer(err_msg)
            return
    elif message.photo:
        file_id = message.photo[-1].file_id
        filename = "design.jpg"
        
    bot = message.bot
    file_info = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file_info.file_path)
    
    await state.update_data(design_file_bytes=file_bytes.read(), filename=filename)
    
    data = await state.get_data()
    pos = data.get("print_position_data") or {}
    requires_multiple = pos.get("requires_multiple_designs", False)
    
    if requires_multiple:
        await state.set_state(OrderingStates.design_file_2)
        if user_lang == "ru":
            prompt_text = (
                "Загрузите ваш макет/изображение для принта (<b>Макет 2 / Сзади</b>):\n\n"
                "<i>Если вы хотите использовать то же самое изображение для второго принта, нажмите кнопку ниже:</i>"
            )
        else:
            prompt_text = (
                "Rasm faylini yuklang (<b>2-rasm / Orqa tomoni</b>):\n\n"
                "<i>Agar ikkinchi tomon uchun ham shu rasmdan foydalanmoqchi bo'lsangiz, quyidagi tugmani bosing:</i>"
            )
        await message.answer(
            prompt_text,
            parse_mode="HTML",
            reply_markup=get_design_2_keyboard(language=user_lang)
        )
    else:
        await state.set_state(OrderingStates.comment)
        prompt_text = (
            "Добавьте комментарий к макету (например, требования по размещению, размеру принта и т.д.):" if user_lang == "ru" else
            "Rasm joylashuvi va o'lchami bo'yicha talablarni (komentariy) qoldiring:"
        )
        await message.answer(
            prompt_text,
            reply_markup=get_comment_skip_keyboard(language=user_lang)
        )

@router.callback_query(F.data == "skip_design_2")
async def skip_design_2_callback(callback: CallbackQuery, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    await state.update_data(design_file_2_bytes=None, filename_2=None)
    await state.set_state(OrderingStates.comment)
    await callback.message.delete()
    
    if user_lang == "ru":
        msg_text = (
            "Вы выбрали использовать то же изображение для второго принта.\n\n"
            "Добавьте комментарий к макету (например, требования по размещению, размеру принта и т.д.):"
        )
    else:
        msg_text = (
            "Ikkinchi tomon uchun ham xuddi shu rasmni tanladingiz.\n\n"
            "Rasm joylashuvi va o'lchami bo'yicha talablarni (komentariy) qoldiring:"
        )
    await callback.message.answer(
        msg_text,
        reply_markup=get_comment_skip_keyboard(language=user_lang)
    )
    await callback.answer()

@router.message(OrderingStates.design_file_2, F.photo | F.document)
async def process_design_file_2(message: Message, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    file_id = None
    filename = "design_2.png"
    
    if message.document:
        file_id = message.document.file_id
        filename = message.document.file_name
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in ["jpg", "jpeg", "png", "pdf", "svg"]:
            err_msg = "Неподдерживаемый формат файла. Загрузите JPG, PNG, PDF или SVG." if user_lang == "ru" else "Qo'llab-quvvatlanmaydigan format. JPG, PNG, PDF yoki SVG yuklang."
            await message.answer(err_msg)
            return
    elif message.photo:
        file_id = message.photo[-1].file_id
        filename = "design_2.jpg"
        
    bot = message.bot
    file_info = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file_info.file_path)
    
    await state.update_data(design_file_2_bytes=file_bytes.read(), filename_2=filename)
    
    await state.set_state(OrderingStates.comment)
    prompt_text = (
        "Добавьте комментарий к макету (например, требования по размещению, размеру принта и т.д.):" if user_lang == "ru" else
        "Rasm joylashuvi va o'lchami bo'yicha talablarni (komentariy) qoldiring:"
    )
    await message.answer(
        prompt_text,
        reply_markup=get_comment_skip_keyboard(language=user_lang)
    )

@router.callback_query(F.data == "skip_comment")
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    await state.update_data(comment="")
    await ask_quantity(callback.message, state)
    await callback.answer()

@router.message(OrderingStates.comment)
async def process_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await ask_quantity(message, state)

async def ask_quantity(message: Message, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        message.chat.id,
        message.chat.username or "",
        message.chat.first_name or ""
    )
    await state.set_state(OrderingStates.quantity)
    builder = InlineKeyboardBuilder()
    for q in [1, 2, 3, 5, 10]:
        builder.button(text=str(q), callback_data=f"qty_{q}")
    builder.adjust(5)
    builder.row(InlineKeyboardButton(text=_t(user_lang, "cancel"), callback_data="cancel_action"))
    
    if user_lang == "ru":
        prompt_text = (
            "🔢 <b>Выберите количество из быстрых вариантов или напишите любое другое число прямо в чат:</b>\n\n"
            "<i>Например: 15, 50, 100</i>"
        )
    else:
        prompt_text = (
            "🔢 <b>Tezkor variantlardan sonini tanlang yoki chatga istalgan boshqa sonni yozib yuboring:</b>\n\n"
            "<i>Masalan: 15, 50, 100</i>"
        )
        
    await message.answer(
        prompt_text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("qty_"))
async def select_quantity_callback(callback: CallbackQuery, state: FSMContext):
    quantity = int(callback.data.split("_")[1])
    await add_product_to_cart(callback.message, state, quantity)
    await callback.answer()

@router.message(OrderingStates.quantity)
async def process_quantity_text(message: Message, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError()
    except ValueError:
        err_msg = "Пожалуйста, введите корректное положительное число." if user_lang == "ru" else "Iltimos, to'g'ri musbat son kiriting."
        await message.answer(err_msg)
        return
        
    await add_product_to_cart(message, state, quantity)

async def add_product_to_cart(message: Message, state: FSMContext, quantity: int):
    user_lang, _ = await get_user_lang_and_manager(
        message.chat.id,
        message.chat.username or "",
        message.chat.first_name or ""
    )
    data = await state.get_data()
    
    res = await api_client.add_to_cart(
        telegram_id=message.chat.id,
        product_id=data["product_id"],
        size_id=data["size_id"],
        color_id=data["color_id"],
        print_position_id=data["print_position_id"],
        quantity=quantity,
        design_file_bytes=data["design_file_bytes"],
        filename=data["filename"],
        design_file_2_bytes=data.get("design_file_2_bytes"),
        filename_2=data.get("filename_2"),
        comment=data.get("comment", "")
    )
    
    if not res or res.get("error"):
        err_msg = "Произошла ошибка при добавлении в корзину. Попробуйте еще раз." if user_lang == "ru" else "Savatchaga qo'shishda xatolik yuz berdi. Qayta urinib ko'ring."
        await message.answer(err_msg)
        logger.error(f"Add to cart error: {res}")
    else:
        success_msg = f"🛒 Товар успешно добавлен в корзину ({quantity} шт.)!" if user_lang == "ru" else f"🛒 Mahsulot savatchaga muvaffaqiyatli qo'shildi ({quantity} dona)!"
        await message.answer(
            success_msg,
            reply_markup=await get_user_main_menu(
                message.chat.id,
                message.chat.username or "",
                message.chat.first_name or ""
            )
        )
    await state.clear()

# =====================================================================
# CART HANDLERS
# =====================================================================

@router.message(F.text.in_({"🛒 Корзина", "🛒 Savatcha"}))
async def show_cart(message: Message):
    user_lang, is_manager = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    cart = await api_client.get_cart(message.from_user.id)
    
    if not cart or cart.get("error"):
        err_msg = "Ошибка получения корзины." if user_lang == "ru" else "Savatchani yuklashda xatolik yuz berdi."
        await message.answer(err_msg)
        return
        
    items = cart.get("items", [])
    if not items:
        empty_msg = "Ваша корзина пуста. Начните покупки в разделе Каталог!" if user_lang == "ru" else "Savatchangiz bo'sh. Katalog bo'limidan xarid qilishni boshlang!"
        await message.answer(empty_msg)
        return
        
    msg = "🛒 <b>Ваша корзина:</b>\n\n" if user_lang == "ru" else "🛒 <b>Sizning savatchangiz:</b>\n\n"
    for idx, item in enumerate(items, 1):
        prod = item["product_details"]
        size = item["size_details"]["name"] if item["size_details"] else "—"
        
        color_data = item["color_details"]
        color = (color_data.get("name_uz") if (user_lang == "uz" and color_data.get("name_uz")) else color_data["name"]) if color_data else "—"
        
        print_pos_data = item["print_position_details"]
        print_pos = (print_pos_data.get("name_uz") if (user_lang == "uz" and print_pos_data.get("name_uz")) else print_pos_data["name"]) if print_pos_data else "—"
        
        prod_title = prod.get("title_uz") if (user_lang == "uz" and prod.get("title_uz")) else prod["title"]
        
        if user_lang == "ru":
            msg += (
                f"<b>{idx}. {prod_title}</b>\n"
                f"📐 Размер: {size} | 🎨 Цвет: {color}\n"
                f"📍 Принт: {print_pos}\n"
                f"🔢 Кол-во: {item['quantity']} шт.\n"
                f"💵 Стоимость: {item['total_price']} руб.\n\n"
            )
        else:
            msg += (
                f"<b>{idx}. {prod_title}</b>\n"
                f"📐 O'lcham: {size} | 🎨 Rang: {color}\n"
                f"📍 Bosma: {print_pos}\n"
                f"🔢 Soni: {item['quantity']} dona\n"
                f"💵 Narxi: {item['total_price']} so'm\n\n"
            )
        
    total_val = cart['total_cart_price']
    total_msg = f"<b>Итого к оплате: {total_val} руб.</b>" if user_lang == "ru" else f"<b>Jami to'lov: {total_val} so'm</b>"
    msg += total_msg
    
    await message.answer(msg, parse_mode="HTML", reply_markup=get_cart_keyboard(items, language=user_lang))

@router.callback_query(F.data.startswith("cart_qty_"))
async def update_cart_item_qty(callback: CallbackQuery):
    parts = callback.data.split("_")
    action = parts[2]  # 'inc' or 'dec'
    item_id = int(parts[3])
    
    # We need to find current quantity of the item
    cart = await api_client.get_cart(callback.from_user.id)
    items = cart.get("items", [])
    item = next((i for i in items if i["id"] == item_id), None)
    
    if not item:
        await callback.answer("Товар не найден.")
        return
        
    new_qty = item["quantity"] + 1 if action == "inc" else item["quantity"] - 1
    
    await api_client.update_cart_item(item_id, new_qty)
    
    # Refresh cart
    await refresh_cart_message(callback)

@router.callback_query(F.data.startswith("cart_del_"))
async def delete_cart_item(callback: CallbackQuery):
    item_id = int(callback.data.split("_")[2])
    await api_client.delete_cart_item(item_id)
    await callback.answer("Товар удален из корзины")
    await refresh_cart_message(callback)

@router.callback_query(F.data == "cart_clear")
async def clear_cart(callback: CallbackQuery):
    user_lang, _ = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    await api_client.clear_cart(callback.from_user.id)
    alert = "Корзина очищена" if user_lang == "ru" else "Savatcha tozalandi"
    empty = "Ваша корзина пуста." if user_lang == "ru" else "Savatchangiz bo'sh."
    await callback.answer(alert)
    await callback.message.delete()
    await callback.message.answer(empty)

async def refresh_cart_message(callback: CallbackQuery):
    user_lang, _ = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    cart = await api_client.get_cart(callback.from_user.id)
    items = cart.get("items", [])
    
    if not items:
        await callback.message.delete()
        empty = "Ваша корзина пуста." if user_lang == "ru" else "Savatchangiz bo'sh."
        await callback.message.answer(empty)
        return
        
    msg = "🛒 <b>Ваша корзина:</b>\n\n" if user_lang == "ru" else "🛒 <b>Sizning savatchangiz:</b>\n\n"
    for idx, item in enumerate(items, 1):
        prod = item["product_details"]
        size = item["size_details"]["name"] if item["size_details"] else "—"
        
        color_data = item["color_details"]
        color = (color_data.get("name_uz") if (user_lang == "uz" and color_data.get("name_uz")) else color_data["name"]) if color_data else "—"
        
        print_pos_data = item["print_position_details"]
        print_pos = (print_pos_data.get("name_uz") if (user_lang == "uz" and print_pos_data.get("name_uz")) else print_pos_data["name"]) if print_pos_data else "—"
        
        prod_title = prod.get("title_uz") if (user_lang == "uz" and prod.get("title_uz")) else prod["title"]
        
        if user_lang == "ru":
            msg += (
                f"<b>{idx}. {prod_title}</b>\n"
                f"📐 Размер: {size} | 🎨 Цвет: {color}\n"
                f"📍 Принт: {print_pos}\n"
                f"🔢 Кол-во: {item['quantity']} шт.\n"
                f"💵 Стоимость: {item['total_price']} руб.\n\n"
            )
        else:
            msg += (
                f"<b>{idx}. {prod_title}</b>\n"
                f"📐 O'lcham: {size} | 🎨 Rang: {color}\n"
                f"📍 Bosma: {print_pos}\n"
                f"🔢 Soni: {item['quantity']} dona\n"
                f"💵 Narxi: {item['total_price']} so'm\n\n"
            )
        
    total_val = cart['total_cart_price']
    total_msg = f"<b>Итого к оплате: {total_val} руб.</b>" if user_lang == "ru" else f"<b>Jami to'lov: {total_val} so'm</b>"
    msg += total_msg
    
    try:
        await callback.message.edit_text(msg, parse_mode="HTML", reply_markup=get_cart_keyboard(items, language=user_lang))
    except Exception:
        pass
    await callback.answer()

# =====================================================================
# CHECKOUT FLOW (FSM)
# =====================================================================

@router.callback_query(F.data == "cart_checkout")
async def checkout_start(callback: CallbackQuery, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    cart = await api_client.get_cart(callback.from_user.id)
    settings_data = await api_client.get_settings()
    
    min_amount = 0.00
    if settings_data and not settings_data.get("error"):
        min_amount = float(settings_data.get("min_order_amount", 0))
        
    total_price = float(cart.get("total_cart_price", 0))
    if total_price < min_amount:
        alert_msg = f"Минимальная сумма заказа: {min_amount} руб. Добавьте еще товаров." if user_lang == "ru" else f"Minimal buyurtma summasi: {min_amount} so'm. Yana mahsulotlar qo'shing."
        await callback.answer(alert_msg, show_alert=True)
        return
        
    await callback.answer()
    await callback.message.delete()
    
    await state.set_state(CheckoutStates.full_name)
    prompt_text = "📝 Введите ваше ФИО для получения заказа:" if user_lang == "ru" else "📝 Buyurtmani olish uchun F.I.Sh. kiriting:"
    await callback.message.answer(
        prompt_text, 
        reply_markup=get_cancel_keyboard(language=user_lang)
    )

@router.message(CheckoutStates.full_name)
async def process_checkout_name(message: Message, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    await state.update_data(full_name=message.text)
    await state.set_state(CheckoutStates.phone)
    prompt_text = "📱 Предоставьте ваш номер телефона (нажмите кнопку ниже или введите вручную):" if user_lang == "ru" else "📱 Telefon raqamingizni yuboring (tugmani bosing yoki qo'lda kiriting):"
    await message.answer(
        prompt_text,
        reply_markup=get_share_phone_keyboard(language=user_lang)
    )

@router.message(CheckoutStates.phone)
async def process_checkout_phone(message: Message, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    phone = message.contact.phone_number if message.contact else message.text
    if not phone or (message.text and message.text.startswith("/")):
        err_msg = "Пожалуйста, введите корректный номер телефона." if user_lang == "ru" else "Iltimos, to'g'ri telefon raqamini kiriting."
        await message.answer(err_msg)
        return
        
    import re
    cleaned_phone = "".join(c for c in phone if c.isdigit() or c == "+")
    if not re.match(r"^\+?\d{9,15}$", cleaned_phone):
        if user_lang == "ru":
            err_msg = (
                "❌ <b>Неверный формат номера телефона.</b>\n\n"
                "Пожалуйста, введите корректный номер телефона (например, <code>+79991234567</code> или <code>89991234567</code>):"
            )
        else:
            err_msg = (
                "❌ <b>Telefon raqami formati noto'g'ri.</b>\n\n"
                "Iltimos, to'g'ri telefon raqamini kiriting (masalan, <code>+998901234567</code>):"
            )
        await message.answer(err_msg, parse_mode="HTML")
        return
        
    await state.update_data(phone=cleaned_phone)
    await state.set_state(CheckoutStates.city)
    prompt_text = "🏙 Введите город доставки:" if user_lang == "ru" else "🏙 Yetkazib berish shahrini kiriting:"
    await message.answer(
        prompt_text,
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(CheckoutStates.city)
async def process_checkout_city(message: Message, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    await state.update_data(city=message.text)
    await state.set_state(CheckoutStates.address)
    prompt_text = "🏠 Введите адрес доставки (улица, дом, квартира/офис):" if user_lang == "ru" else "🏠 Yetkazib berish manzilini kiriting (ko'cha, uy, xonadon/ofis):"
    await message.answer(
        prompt_text,
        reply_markup=get_cancel_keyboard(language=user_lang)
    )

@router.message(CheckoutStates.address)
async def process_checkout_address(message: Message, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    await state.update_data(address=message.text)
    
    data = await state.get_data()
    cart = await api_client.get_cart(message.chat.id)
    
    if user_lang == "ru":
        msg = (
            f"📋 <b>Проверьте данные вашего заказа:</b>\n\n"
            f"<b>Получатель:</b> {data['full_name']}\n"
            f"<b>Телефон:</b> {data['phone']}\n"
            f"<b>Доставка:</b> г. {data['city']}, {data['address']}\n\n"
            f"<b>Сумма заказа:</b> {cart['total_cart_price']} руб.\n"
        )
    else:
        msg = (
            f"📋 <b>Buyurtma ma'lumotlarini tekshiring:</b>\n\n"
            f"<b>Qabul qiluvchi:</b> {data['full_name']}\n"
            f"<b>Telefon:</b> {data['phone']}\n"
            f"<b>Etkazib berish:</b> {data['city']} sh., {data['address']}\n\n"
            f"<b>Buyurtma summasi:</b> {cart['total_cart_price']} so'm\n"
        )
    
    await message.answer(msg, parse_mode="HTML", reply_markup=get_checkout_confirm_keyboard(language=user_lang))

@router.message(F.text.in_({"❌ Отменить оформление", "❌ Rasmiylashtirishni bekor qilish"}))
async def cancel_checkout_message(message: Message, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    await state.clear()
    msg_text = "Оформление заказа отменено." if user_lang == "ru" else "Buyurtma berish bekor qilindi."
    await message.answer(
        msg_text, 
        reply_markup=await get_user_main_menu(
            message.from_user.id, 
            message.from_user.username, 
            message.from_user.first_name
        )
    )

@router.callback_query(F.data == "checkout_confirm")
async def checkout_confirm(callback: CallbackQuery, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    data = await state.get_data()
    
    required_keys = ["full_name", "phone", "address", "city"]
    if not all(k in data for k in required_keys):
        err_msg = "Сессия оформления заказа истекла. Пожалуйста, оформите заказ заново из корзины." if user_lang == "ru" else "Buyurtma berish seansi tugadi. Iltimos, savatchadan boshidan urinib ko'ring."
        await callback.answer(err_msg, show_alert=True)
        try:
            await callback.message.delete()
        except Exception:
            pass
        return
        
    order = await api_client.checkout(
        telegram_id=callback.from_user.id,
        full_name=data["full_name"],
        phone=data["phone"],
        address=data["address"],
        city=data["city"]
    )

    await state.clear()
    await callback.message.delete()
    
    if not order or order.get("error"):
        err_msg = "Произошла ошибка при оформлении заказа. Свяжитесь с поддержкой." if user_lang == "ru" else "Buyurtma berishda xatolik yuz berdi. Yordam xizmati bilan bog'laning."
        await callback.message.answer(
            err_msg,
            reply_markup=await get_user_main_menu(
                callback.from_user.id, 
                callback.from_user.username, 
                callback.from_user.first_name
            )
        )
        logger.error(f"Checkout error: {order}")
        return
        
    await show_payment_methods(callback.message, order)
    await callback.answer()

async def show_payment_methods(message: Message, order: dict):
    user_lang, _ = await get_user_lang_and_manager(
        message.chat.id,
        message.chat.username or "",
        message.chat.first_name or ""
    )
    payment_methods = await api_client.get_payment_methods()
    
    if user_lang == "ru":
        msg = (
            f"🎉 <b>Заказ № {order['order_number']} оформлен!</b>\n\n"
            f"Сумма к оплате: <b>{order['total_price']} руб.</b>\n\n"
            f"<b>Реквизиты для оплаты:</b>\n"
        )
    else:
        msg = (
            f"🎉 <b>Buyurtma № {order['order_number']} rasmiylashtirildi!</b>\n\n"
            f"To'lov summasi: <b>{order['total_price']} so'm</b>\n\n"
            f"<b>To'lov rekvizitlari:</b>\n"
        )
    
    if payment_methods and not isinstance(payment_methods, dict):
        for pm in payment_methods:
            msg += f"🔹 {pm['title']}\n💳 Номер: <code>{pm['card_number']}</code>\n👤 Получатель: {pm['receiver_name']}\n\n"
    else:
        if user_lang == "ru":
            msg += "Свяжитесь с поддержкой для получения реквизитов.\n\n"
        else:
            msg += "Rekvizitlarni olish uchun yordam xizmatiga bog'laning.\n\n"
        
    if user_lang == "ru":
        msg += "После оплаты нажмите кнопку ниже и отправьте чек (скриншот)."
    else:
        msg += "To'lovni to'lagach, quyidagi tugmani bosing va chekni (skrinshot) yuboring."
    
    await message.answer(msg, parse_mode="HTML", reply_markup=get_pay_payment_keyboard(order["id"], language=user_lang))

# =====================================================================
# PAYMENT & RECEIPTS FLOW
# =====================================================================

@router.callback_query(F.data.startswith("pay_paid_"))
async def pay_paid_click(callback: CallbackQuery, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name
    )
    order_id = int(callback.data.split("_")[2])
    await state.update_data(order_id=order_id)
    await state.set_state(ReceiptStates.waiting_for_receipt)
    
    await callback.message.delete()
    prompt_text = "📸 Пожалуйста, отправьте скриншот/фото чека об оплате:" if user_lang == "ru" else "📸 Iltimos, to'lov cheki rasmini/skrinshotini yuboring:"
    await callback.message.answer(
        prompt_text,
        reply_markup=get_cancel_keyboard(language=user_lang)
    )
    await callback.answer()

@router.message(ReceiptStates.waiting_for_receipt, F.photo | F.document)
async def process_receipt_upload(message: Message, state: FSMContext):
    user_lang, _ = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    file_id = None
    filename = "receipt.jpg"
    
    if message.photo:
        file_id = message.photo[-1].file_id
        filename = "receipt.jpg"
    elif message.document:
        file_id = message.document.file_id
        filename = message.document.file_name
        
    if not file_id:
        err_msg = "Отправьте чек в виде фото или документа." if user_lang == "ru" else "Chekni rasm yoki hujjat ko'rinishida yuboring."
        await message.answer(err_msg)
        return
        
    bot = message.bot
    file_info = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file_info.file_path)
    
    data = await state.get_data()
    order_id = data["order_id"]
    
    res = await api_client.upload_receipt(
        order_id=order_id,
        receipt_bytes=file_bytes.read(),
        filename=filename
    )
    
    await state.clear()
    
    if not res or res.get("error"):
        err_msg = "Ошибка при отправке чека. Попробуйте повторить через меню Мои заказы." if user_lang == "ru" else "Chekni yuborishda xatolik. Mening buyurtmalarim bo'limidan qayta urinib ko'ring."
        await message.answer(
            err_msg,
            reply_markup=await get_user_main_menu(
                message.from_user.id, 
                message.from_user.username, 
                message.from_user.first_name
            )
        )
        logger.error(f"Receipt upload error: {res}")
    else:
        success_msg = "✅ Чек отправлен на проверку. Мы уведомим вас о подтверждении оплаты." if user_lang == "ru" else "✅ Chek tekshirish uchun yuborildi. To'lov tasdiqlangach sizga xabar beramiz."
        await message.answer(
            success_msg,
            reply_markup=await get_user_main_menu(
                message.from_user.id, 
                message.from_user.username, 
                message.from_user.first_name
            )
        )

# =====================================================================
# MY ORDERS
# =====================================================================

@router.message(F.text.in_({"📦 Мои заказы", "📦 Mening buyurtmalarim"}))
async def show_my_orders(message: Message):
    user_lang, is_manager = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    orders = await api_client.get_orders(message.chat.id)
    
    if not orders or (isinstance(orders, dict) and orders.get("error")):
        err_msg = "Ошибка получения списка заказов." if user_lang == "ru" else "Buyurtmalar ro'yxatini yuklashda xatolik yuz berdi."
        await message.answer(err_msg)
        return
        
    if not orders:
        no_orders_msg = _t(user_lang, "no_orders")
        await message.answer(no_orders_msg)
        return
        
    msg = _t(user_lang, "my_orders_title")
    builder = InlineKeyboardBuilder()
    has_pending = False
    
    for order in orders:
        status_disp = order["status_display"]
        created = order["created_at"][:10]  # Take date only
        if user_lang == "ru":
            msg += (
                f"🔸 <b>Заказ:</b> {order['order_number']}\n"
                f"📅 Дата: {created}\n"
                f"💵 Сумма: {order['total_price']} руб.\n"
                f"⚙️ Статус: <b>{status_disp}</b>\n\n"
            )
        else:
            # Let's map display status to Uzbek if needed, or keep standard display. Let's do simple translation of status displays
            uz_status = status_disp
            if order["status"] == "NEW":
                uz_status = "Yangi"
            elif order["status"] == "WAITING_PAYMENT":
                uz_status = "To'lov kutilmoqda"
            elif order["status"] == "RECEIPT_PENDING":
                uz_status = "Chek tekshirilmoqda"
            elif order["status"] == "PAID":
                uz_status = "To'langan"
            elif order["status"] == "IN_PRODUCTION":
                uz_status = "Tayyorlanmoqda"
            elif order["status"] == "CANCELLED":
                uz_status = "Bekor qilingan"
                
            msg += (
                f"🔸 <b>Buyurtma:</b> {order['order_number']}\n"
                f"📅 Sana: {created}\n"
                f"💵 Summa: {order['total_price']} so'm\n"
                f"⚙️ Holati: <b>{uz_status}</b>\n\n"
            )
            
        if order["status"] == "WAITING_PAYMENT":
            btn_text = _t(user_lang, "pay_order", order_number=order['order_number'])
            builder.button(text=btn_text, callback_data=f"pay_paid_{order['id']}")
            has_pending = True
            
    builder.adjust(1)
    
    if has_pending:
        await message.answer(msg, parse_mode="HTML", reply_markup=builder.as_markup())
    else:
        await message.answer(msg, parse_mode="HTML")

# =====================================================================
# ADMIN RECEIPT VERIFICATION CALLBACK
# =====================================================================

@router.callback_query(F.data.startswith("verify_receipt_"))
async def admin_verify_receipt(callback: CallbackQuery):
    parts = callback.data.split("_")
    action = parts[2]      # 'approve' or 'reject'
    receipt_id = int(parts[3])
    
    # Send verification request to Django API using the bot's token as authorization
    res = await api_client.verify_receipt(
        receipt_id=receipt_id,
        action=action,
        token=settings.bot_token
    )
    
    if not res or res.get("error"):
        await callback.answer("Ошибка при обработке запроса. Возможно, нет связи с сервером.", show_alert=True)
        logger.error(f"Receipt verification failed: {res}")
        return
        
    status_text = "✅ Оплата подтверждена" if action == "approve" else "❌ Чек отклонен"
    
    # Update the admin's notification message to remove buttons and show decision
    caption = callback.message.caption or callback.message.text or ""
    new_caption = f"{caption}\n\n<b>Решение: {status_text}</b>"
    
    if callback.message.photo:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
    else:
        await callback.message.edit_text(text=new_caption, parse_mode="HTML", reply_markup=None)
        
    await callback.answer(f"Чек успешно { 'подтвержден' if action == 'approve' else 'отклонен' }.")

# =====================================================================
# MANAGER / ADMIN HANDLERS
# =====================================================================

@router.message(F.text.in_({"⚙️ Панель менеджера", "⚙️ Menejer paneli"}))
async def show_manager_panel(message: Message):
    client_info = await api_client.register_client(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    if client_info and client_info.get("is_manager"):
        await message.answer(
            "🛠 <b>Панель менеджера</b>\n\nЗдесь вы можете управлять заказами и просматривать финансовую статистику.",
            parse_mode="HTML",
            reply_markup=get_manager_menu_keyboard()
        )
    else:
        await message.answer("У вас нет прав доступа к этой панели.")

@router.message(F.text == "👤 Режим клиента")
async def manager_client_mode(message: Message):
    await message.answer(
        "Переключено в режим клиента.",
        reply_markup=await get_user_main_menu(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name
        )
    )

@router.message(F.text == "📋 Новые заказы")
async def manager_new_orders(message: Message):
    # Check permission
    client_info = await api_client.register_client(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if not client_info or not client_info.get("is_manager"):
        await message.answer("Доступ запрещен.")
        return

    # Fetch orders waiting for payment or verification
    orders = await api_client.get_orders(message.from_user.id)
    if not orders or (isinstance(orders, dict) and orders.get("error")):
        await message.answer("Ошибка получения списка заказов.")
        return

    # Filter to display new orders (WAITING_PAYMENT and RECEIPT_PENDING)
    new_orders = [o for o in orders if o["status"] in ["WAITING_PAYMENT", "RECEIPT_PENDING"]]
    
    if not new_orders:
        await message.answer("Нет новых заказов, ожидающих оплаты или проверки чеков.")
        return

    msg = "📋 <b>Новые заказы ({})</b>\n\n".format(len(new_orders))
    for order in new_orders:
        status_disp = order["status_display"]
        created = order["created_at"][:10]
        msg += (
            f"🔸 <b>Заказ:</b> {order['order_number']}\n"
            f"📅 Дата: {created}\n"
            f"👤 Клиент: {order['full_name']} (@{order['client_details']['username'] or ''})\n"
            f"📞 Телефон: {order['phone']}\n"
            f"💵 Сумма: {order['total_price']} руб.\n"
            f"⚙️ Статус: <b>{status_disp}</b>\n\n"
        )
    
    await message.answer(msg, parse_mode="HTML")

@router.message(F.text == "📦 В работе")
async def manager_active_orders(message: Message):
    # Check permission
    client_info = await api_client.register_client(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if not client_info or not client_info.get("is_manager"):
        await message.answer("Доступ запрещен.")
        return

    # Fetch all orders
    orders = await api_client.get_orders(message.from_user.id)
    if not orders or (isinstance(orders, dict) and orders.get("error")):
        await message.answer("Ошибка получения списка заказов.")
        return

    # Filter to active/processing orders
    active_orders = [o for o in orders if o["status"] in ["PAID", "IN_PRODUCTION", "PRINTED", "PACKED", "SHIPPED"]]
    
    if not active_orders:
        await message.answer("Нет активных заказов в производстве/доставке.")
        return

    msg = "📦 <b>Активные заказы в работе ({})</b>\n\n".format(len(active_orders))
    for order in active_orders:
        status_disp = order["status_display"]
        created = order["created_at"][:10]
        msg += (
            f"🔸 <b>Заказ:</b> {order['order_number']}\n"
            f"📅 Дата: {created}\n"
            f"👤 Клиент: {order['full_name']} (@{order['client_details']['username'] or ''})\n"
            f"💵 Сумма: {order['total_price']} руб.\n"
            f"⚙️ Статус: <b>{status_disp}</b>\n\n"
        )
    
    await message.answer(msg, parse_mode="HTML")

@router.message(F.text == "📊 Статистика")
async def manager_stats(message: Message):
    # Check permission
    client_info = await api_client.register_client(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if not client_info or not client_info.get("is_manager"):
        await message.answer("Доступ запрещен.")
        return

    stats = await api_client.get_manager_stats(message.from_user.id)
    if not stats or (isinstance(stats, dict) and stats.get("error")):
        await message.answer("Ошибка получения финансовой статистики.")
        return

    msg = (
        f"📊 <b>Финансовая статистика магазина</b>\n\n"
        f"👥 Всего зарегистрировано клиентов: <b>{stats['total_clients']}</b>\n"
        f"📦 Всего оформлено заказов: <b>{stats['total_orders']}</b>\n\n"
        f"💵 Суммарная выручка (оплаченные): <b>{stats['revenue']:.2f} руб.</b>\n"
        f"🧾 Чеков ожидает проверки: <b>{stats['new_receipts']}</b>\n"
        f"⚙️ Заказов в производстве: <b>{stats['in_production']}</b>"
    )
    
    await message.answer(msg, parse_mode="HTML")


# =====================================================================
# OTHER SERVICES FLOW
# =====================================================================

@router.message(F.text.in_({"💼 Другие услуги", "💼 Boshqa xizmatlar"}))
async def other_services_start(message: Message, state: FSMContext):
    await state.clear()
    user_lang, is_manager = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    await state.set_state(OtherServicesStates.comment)
    await message.answer(
        _t(user_lang, "other_services_prompt"),
        reply_markup=get_cancel_keyboard(language=user_lang)
    )

@router.message(OtherServicesStates.comment)
async def other_services_comment_receive(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/"):
        return # Ignore commands
        
    await state.update_data(comment=message.text)
    await state.set_state(OtherServicesStates.phone)
    
    user_lang, is_manager = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    await message.answer(
        _t(user_lang, "other_services_phone"),
        reply_markup=get_share_phone_keyboard(language=user_lang)
    )

@router.message(OtherServicesStates.phone)
@router.message(OtherServicesStates.phone, F.contact)
async def other_services_phone_receive(message: Message, state: FSMContext):
    user_lang, is_manager = await get_user_lang_and_manager(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    phone = ""
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        if message.text.startswith("/"):
            return # Ignore commands
        if message.text == _t(user_lang, "cancel_checkout"):
            await state.clear()
            await message.answer(
                _t(user_lang, "back_to_menu"),
                reply_markup=await get_user_main_menu(
                    message.from_user.id,
                    message.from_user.username,
                    message.from_user.first_name
                )
            )
            return
        phone = message.text
        
    if not phone:
        await message.answer(_t(user_lang, "other_services_phone"))
        return
        
    data = await state.get_data()
    comment = data.get("comment", "")
    
    res = await api_client.submit_other_services(
        telegram_id=message.from_user.id,
        comment=comment,
        phone=phone
    )
    
    await state.clear()
    
    if res and not res.get("error"):
        await message.answer(
            _t(user_lang, "other_services_success"),
            reply_markup=await get_user_main_menu(
                message.from_user.id,
                message.from_user.username,
                message.from_user.first_name
            )
        )
    else:
        await message.answer(
            "Произошла ошибка при отправке заявки. Пожалуйста, попробуйте позже.",
            reply_markup=await get_user_main_menu(
                message.from_user.id,
                message.from_user.username,
                message.from_user.first_name
            )
        )


