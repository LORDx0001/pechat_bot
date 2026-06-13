from django.contrib import admin
from django.utils.html import format_html
from .models import Cart, CartItem, Order, OrderItem, PaymentMethod, Receipt
from .tasks import send_telegram_notification_task

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'size', 'color', 'print_position', 'quantity', 'design_file', 'design_file_2', 'comment', 'item_price')

class ReceiptInline(admin.TabularInline):
    model = Receipt
    extra = 0
    readonly_fields = ('image_preview', 'status', 'created_at')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="100" /></a>', obj.image.url)
        return "Нет фото"
    image_preview.short_description = "Превью чека"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'client', 'full_name', 'phone', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'phone', 'full_name', 'client__username', 'client__first_name', 'client__telegram_id')
    readonly_fields = ('order_number', 'client', 'total_price', 'created_at')
    inlines = [OrderItemInline, ReceiptInline]
    
    actions = ['set_status_in_production', 'set_status_printed', 'set_status_packed', 'set_status_shipped', 'set_status_completed', 'set_status_cancelled']

    def set_status_in_production(self, request, queryset):
        rows_updated = queryset.update(status='IN_PRODUCTION')
        for order in queryset:
            send_telegram_notification_task.delay('status_changed', order.id)
        self.message_user(request, f"Статус {rows_updated} заказов изменен на 'В производстве'.")
    set_status_in_production.short_description = "Изменить статус на: В производстве"

    def set_status_printed(self, request, queryset):
        rows_updated = queryset.update(status='PRINTED')
        for order in queryset:
            send_telegram_notification_task.delay('status_changed', order.id)
        self.message_user(request, f"Статус {rows_updated} заказов изменен на 'Напечатан'.")
    set_status_printed.short_description = "Изменить статус на: Напечатан"

    def set_status_packed(self, request, queryset):
        rows_updated = queryset.update(status='PACKED')
        for order in queryset:
            send_telegram_notification_task.delay('status_changed', order.id)
        self.message_user(request, f"Статус {rows_updated} заказов изменен на 'Упакован'.")
    set_status_packed.short_description = "Изменить статус на: Упакован"

    def set_status_shipped(self, request, queryset):
        rows_updated = queryset.update(status='SHIPPED')
        for order in queryset:
            send_telegram_notification_task.delay('status_changed', order.id)
        self.message_user(request, f"Статус {rows_updated} заказов изменен на 'Отправлен'.")
    set_status_shipped.short_description = "Изменить статус на: Отправлен"

    def set_status_completed(self, request, queryset):
        rows_updated = queryset.update(status='COMPLETED')
        for order in queryset:
            send_telegram_notification_task.delay('status_changed', order.id)
        self.message_user(request, f"Статус {rows_updated} заказов изменен на 'Завершен'.")
    set_status_completed.short_description = "Изменить статус на: Завершен"

    def set_status_cancelled(self, request, queryset):
        rows_updated = queryset.update(status='CANCELLED')
        for order in queryset:
            send_telegram_notification_task.delay('status_changed', order.id)
        self.message_user(request, f"Статус {rows_updated} заказов изменен на 'Отменен'.")
    set_status_cancelled.short_description = "Изменить статус на: Отменен"

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('title', 'card_number', 'receiver_name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'card_number', 'receiver_name')

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('order', 'image_preview', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number', 'order__client__first_name')
    readonly_fields = ('order', 'image', 'created_at')
    actions = ['approve_receipts', 'reject_receipts']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="100" /></a>', obj.image.url)
        return "Нет фото"
    image_preview.short_description = "Чек"

    def approve_receipts(self, request, queryset):
        for receipt in queryset:
            receipt.status = 'approved'
            receipt.save()
            order = receipt.order
            order.status = 'PAID'
            order.save()
            send_telegram_notification_task.delay('payment_approved', order.id)
        self.message_user(request, f"Выбранные чеки ({queryset.count()}) подтверждены, заказы переведены в статус 'Оплачен'.")
    approve_receipts.short_description = "Подтвердить выбранные чеки (Оплата получена)"

    def reject_receipts(self, request, queryset):
        for receipt in queryset:
            receipt.status = 'rejected'
            receipt.save()
            order = receipt.order
            order.status = 'WAITING_PAYMENT'
            order.save()
            order.restore_items_to_cart()
            send_telegram_notification_task.delay('payment_rejected', order.id)
        self.message_user(request, f"Выбранные чеки ({queryset.count()}) отклонены, заказы переведены в статус 'Ожидает оплаты' и товары возвращены в корзины клиентов.")
    reject_receipts.short_description = "Отклонить выбранные чеки (Оплата не получена)"

admin.site.register(Cart)
admin.site.register(CartItem)
