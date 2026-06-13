from django.contrib import admin
from django.db.models import Sum, Count, Q
from .models import Client, StoreSettings

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'username', 'telegram_id', 'phone', 'is_manager', 'orders_count_display', 'total_spent_display', 'created_at')
    list_editable = ('is_manager',)
    search_fields = ('first_name', 'username', 'telegram_id', 'phone')
    readonly_fields = ('created_at', 'orders_count_display', 'total_spent_display')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _orders_count=Count('orders', distinct=True),
            _total_spent=Sum('orders__total_price', filter=Q(orders__status__in=[
                'PAID', 'IN_PRODUCTION', 'PRINTED', 'PACKED', 'SHIPPED', 'DELIVERED', 'COMPLETED'
            ]))
        )

    def orders_count_display(self, obj):
        return getattr(obj, '_orders_count', 0)
    orders_count_display.short_description = "Количество заказов"
    orders_count_display.admin_order_field = "_orders_count"

    def total_spent_display(self, obj):
        val = getattr(obj, '_total_spent', 0)
        return f"{val or 0:.2f}"
    total_spent_display.short_description = "Сумма покупок"
    total_spent_display.admin_order_field = "_total_spent"

@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Only allow creating if none exist
        return not StoreSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
