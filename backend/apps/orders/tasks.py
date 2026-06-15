import os
import json
import requests
import threading
from django.conf import settings
from apps.users.models import StoreSettings, Client
from apps.orders.models import Order, Receipt

def _send_telegram_notification_task_impl(notification_type, order_id, receipt_id=None, comment=None):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        print("TELEGRAM_BOT_TOKEN is not configured in Django settings.")
        return

    try:
        order = Order.objects.select_related('client').get(id=order_id)
    except Order.DoesNotExist:
        print(f"Order {order_id} not found.")
        return

    store_settings = StoreSettings.load()
    admin_chat_id = store_settings.admin_chat_id
    client_chat_id = order.client.telegram_id

    base_url = f"https://api.telegram.org/bot{bot_token}"

    # Find all managers/admins
    manager_chat_ids = list(Client.objects.filter(is_manager=True).values_list('telegram_id', flat=True))
    recipients = set()
    if admin_chat_id:
        try:
            recipients.add(int(admin_chat_id))
        except ValueError:
            pass
    for mc_id in manager_chat_ids:
        if mc_id:
            try:
                recipients.add(int(mc_id))
            except ValueError:
                pass

    if notification_type == 'new_order':
        # Build items summary
        items_summary = ""
        for item in order.items.select_related('product', 'size', 'color', 'print_position').all():
            items_summary += (
                f"• <b>{item.product.title if item.product else 'Удаленный товар'}</b>\n"
                f"  Размер: {item.size.name if item.size else '—'}, "
                f"Цвет: {item.color.name if item.color else '—'}, "
                f"Нанесение: {item.print_position.name if item.print_position else '—'}\n"
                f"  Кол-во: {item.quantity} шт. × {item.item_price} руб.\n"
            )
            if item.comment:
                items_summary += f"  📝 <b>Описание:</b> {item.comment}\n"
            if item.design_file:
                backend_url = os.getenv('BACKEND_URL', 'https://pechat.lordx.uz').rstrip('/')
                items_summary += f"  🖼 <a href='{backend_url}{item.design_file.url}'>Скачать макет 1</a>\n"
            if item.design_file_2:
                backend_url = os.getenv('BACKEND_URL', 'https://pechat.lordx.uz').rstrip('/')
                items_summary += f"  🖼 <a href='{backend_url}{item.design_file_2.url}'>Скачать макет 2</a>\n"
            items_summary += "\n"

        message = (
            f"🔔 <b>Новый заказ!</b>\n\n"
            f"<b>Номер заказа:</b> {order.order_number}\n"
            f"<b>Клиент:</b> {order.client.first_name} (@{order.client.username or ''})\n"
            f"<b>ФИО:</b> {order.full_name}\n"
            f"<b>Телефон:</b> {order.phone}\n"
            f"<b>Адрес:</b> {order.city}, {order.address}\n"
            f"<b>Сумма:</b> {order.total_price} {store_settings.currency}\n\n"
            f"📋 <b>Состав заказа:</b>\n{items_summary}"
            f"🔗 <a href='{backend_url}/admin/orders/order/{order.id}/change/'>Открыть заказ в админке</a>"
        )
        
        # Do not notify managers on new_order; wait until payment receipt is uploaded.
        pass
        
        # Notify client
        lang = getattr(order.client, "language", "ru")
        if lang == "uz":
            client_message = (
                f"🎉 <b>Buyurtmangiz muvaffaqiyatli yaratildi!</b>\n\n"
                f"<b>Buyurtma raqami:</b> {order.order_number}\n"
                f"<b>To'lov summasi:</b> {order.total_price} {store_settings.currency}\n\n"
                f"Iltimos, botdagi rekvizitlar orqali to'lovni amalga oshiring va chekni yuboring."
            )
        else:
            client_message = (
                f"🎉 <b>Ваш заказ успешно создан!</b>\n\n"
                f"<b>Номер заказа:</b> {order.order_number}\n"
                f"<b>Сумма к оплате:</b> {order.total_price} {store_settings.currency}\n\n"
                f"Пожалуйста, оплатите заказ по реквизитам в боте и отправьте чек."
            )
        requests.post(f"{base_url}/sendMessage", json={
            "chat_id": client_chat_id,
            "text": client_message,
            "parse_mode": "HTML"
        })

    elif notification_type == 'new_receipt':
        if not receipt_id:
            return
        try:
            receipt = Receipt.objects.get(id=receipt_id)
        except Receipt.DoesNotExist:
            return

        # Build items summary
        items_summary = ""
        for item in order.items.select_related('product', 'size', 'color', 'print_position').all():
            items_summary += (
                f"• <b>{item.product.title if item.product else 'Удаленный товар'}</b>\n"
                f"  Размер: {item.size.name if item.size else '—'}, "
                f"Цвет: {item.color.name if item.color else '—'}, "
                f"Нанесение: {item.print_position.name if item.print_position else '—'}\n"
                f"  Кол-во: {item.quantity} шт. × {item.item_price} руб.\n"
            )
            if item.comment:
                items_summary += f"  📝 <b>Описание:</b> {item.comment}\n"
            if item.design_file:
                backend_url = os.getenv('BACKEND_URL', 'https://pechat.lordx.uz').rstrip('/')
                items_summary += f"  🖼 <a href='{backend_url}{item.design_file.url}'>Скачать макет 1</a>\n"
            if item.design_file_2:
                backend_url = os.getenv('BACKEND_URL', 'https://pechat.lordx.uz').rstrip('/')
                items_summary += f"  🖼 <a href='{backend_url}{item.design_file_2.url}'>Скачать макет 2</a>\n"
            items_summary += "\n"

        message = (
            f"🧾 <b>Новый чек на проверку!</b>\n\n"
            f"<b>Номер заказа:</b> {order.order_number}\n"
            f"<b>Клиент:</b> {order.client.first_name} (@{order.client.username or ''})\n"
            f"<b>ФИО:</b> {order.full_name}\n"
            f"<b>Телефон:</b> {order.phone}\n"
            f"<b>Адрес:</b> {order.city}, {order.address}\n"
            f"<b>Сумма:</b> {order.total_price} {store_settings.currency}\n\n"
            f"📋 <b>Состав заказа:</b>\n{items_summary}"
            f"🔗 <a href='{backend_url}/admin/orders/order/{order.id}/change/'>Открыть заказ в админке</a>"
        )
        
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Подтвердить", "callback_data": f"verify_receipt_approve_{receipt.id}"},
                    {"text": "❌ Отклонить", "callback_data": f"verify_receipt_reject_{receipt.id}"}
                ]
            ]
        }
        
        file_path = receipt.image.path
        for chat_id in recipients:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    requests.post(f"{base_url}/sendPhoto", files={
                        "photo": f
                    }, data={
                        "chat_id": chat_id,
                        "caption": message,
                        "parse_mode": "HTML",
                        "reply_markup": json.dumps(inline_keyboard)
                    })
            else:
                requests.post(f"{base_url}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": message + "\n(Изображение чека не найдено на сервере)",
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(inline_keyboard)
                })


    elif notification_type == 'client_receipt_uploaded':
        lang = getattr(order.client, "language", "ru")
        if lang == "uz":
            client_message = (
                f"🧾 <b>{order.order_number}-sonli buyurtma cheki tekshirish uchun yuborildi.</b>\n"
                f"Administrator to'lovni tasdiqlashi bilan sizga xabar beramiz."
            )
        else:
            client_message = (
                f"🧾 <b>Чек к заказу {order.order_number} отправлен на проверку.</b>\n"
                f"Мы пришлем уведомление, как только администратор подтвердит оплату."
            )
        requests.post(f"{base_url}/sendMessage", json={
            "chat_id": client_chat_id,
            "text": client_message,
            "parse_mode": "HTML"
        })

    elif notification_type == 'payment_approved':
        lang = getattr(order.client, "language", "ru")
        if lang == "uz":
            client_message = (
                f"✅ <b>{order.order_number}-sonli buyurtma uchun to'lov muvaffaqiyatli tasdiqlandi!</b>\n"
                f"Buyurtma holati o'zgartirildi: <b>To'langan</b>.\n"
                f"Biz ishlab chiqarishni boshladik!"
            )
        else:
            client_message = (
                f"✅ <b>Оплата по заказу {order.order_number} успешно подтверждена!</b>\n"
                f"Статус заказа изменен на: <b>Оплачен</b>.\n"
                f"Мы уже начали производство!"
            )
        requests.post(f"{base_url}/sendMessage", json={
            "chat_id": client_chat_id,
            "text": client_message,
            "parse_mode": "HTML"
        })

    elif notification_type == 'payment_rejected':
        lang = getattr(order.client, "language", "ru")
        if lang == "uz":
            client_message = (
                f"❌ <b>{order.order_number}-sonli buyurtma uchun to'lov rad etildi.</b>\n"
            )
            if comment:
                client_message += f"\n<b>Sabab:</b> {comment}\n"
            else:
                client_message += f"\nQo'llab-quvvatlash xizmati bilan bog'laning yoki chekni qayta yuboring."
        else:
            client_message = (
                f"❌ <b>Оплата по заказу {order.order_number} отклонена.</b>\n"
            )
            if comment:
                client_message += f"\n<b>Причина:</b> {comment}\n"
            else:
                client_message += f"\nПожалуйста, свяжитесь с поддержкой или отправьте верный чек повторно."
        requests.post(f"{base_url}/sendMessage", json={
            "chat_id": client_chat_id,
            "text": client_message,
            "parse_mode": "HTML"
        })

    elif notification_type == 'status_changed':
        lang = getattr(order.client, "language", "ru")
        if lang == "uz":
            STATUS_UZ = {
                'NEW': 'Yangi',
                'WAITING_PAYMENT': 'To\'lov kutilmoqda',
                'RECEIPT_PENDING': 'Chek yuborilgan',
                'PAID': 'To\'langan',
                'IN_PRODUCTION': 'Ishlab chiqarilmoqda',
                'PRINTED': 'Chop etilgan',
                'PACKED': 'Qadoqlangan',
                'SHIPPED': 'Yuborilgan',
                'DELIVERED': 'Yetkazib berilgan',
                'COMPLETED': 'Yakunlangan',
                'CANCELLED': 'Bekor qilingan',
            }
            status_display = STATUS_UZ.get(order.status, order.status)
            client_message = (
                f"📦 <b>{order.order_number}-sonli buyurtma holati o'zgardi!</b>\n\n"
                f"Yangi holat: <b>{status_display}</b>"
            )
            if order.status == 'CANCELLED' and comment:
                client_message += f"\n\n<b>Izoh:</b> {comment}"
        else:
            client_message = (
                f"📦 <b>Статус заказа {order.order_number} изменился!</b>\n\n"
                f"Новый статус: <b>{order.get_status_display()}</b>"
            )
            if order.status == 'CANCELLED' and comment:
                client_message += f"\n\n<b>Комментарий менеджера:</b> {comment}"
        requests.post(f"{base_url}/sendMessage", json={
            "chat_id": client_chat_id,
            "text": client_message,
            "parse_mode": "HTML"
        })

class NotificationTask:
    def delay(self, *args, **kwargs):
        threading.Thread(
            target=_send_telegram_notification_task_impl, 
            args=args, 
            kwargs=kwargs
        ).start()

send_telegram_notification_task = NotificationTask()


def send_other_services_notification(client, comment, phone):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        return
        
    store_settings = StoreSettings.load()
    admin_chat_id = store_settings.admin_chat_id
    
    manager_chat_ids = list(Client.objects.filter(is_manager=True).values_list('telegram_id', flat=True))
    recipients = set()
    if admin_chat_id:
        try:
            recipients.add(int(admin_chat_id))
        except ValueError:
            pass
    for mc_id in manager_chat_ids:
        if mc_id:
            try:
                recipients.add(int(mc_id))
            except ValueError:
                pass
                
    base_url = f"https://api.telegram.org/bot{bot_token}"
    message = (
        f"💼 <b>Новая заявка на другие услуги!</b>\n\n"
        f"<b>Клиент:</b> {client.first_name} (@{client.username or ''})\n"
        f"<b>Телефон:</b> {phone}\n"
        f"<b>Описание/Комментарий:</b>\n{comment}"
    )
    
    def run():
        for chat_id in recipients:
            try:
                requests.post(f"{base_url}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                })
            except Exception as e:
                print(f"Error sending other services notification: {e}")
                
    threading.Thread(target=run).start()

