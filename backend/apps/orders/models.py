import uuid
import datetime
from django.db import models
from apps.users.models import Client
from apps.products.models import Product, Size, Color, PrintPosition

def generate_order_number():
    date_str = datetime.date.today().strftime('%Y%m%d')
    random_str = uuid.uuid4().hex[:6].upper()
    return f"ORD-{date_str}-{random_str}"

class Cart(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="cart", verbose_name="Клиент")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"Корзина {self.client}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name="Корзина")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    size = models.ForeignKey(Size, on_delete=models.CASCADE, verbose_name="Размер")
    color = models.ForeignKey(Color, on_delete=models.CASCADE, verbose_name="Цвет")
    print_position = models.ForeignKey(PrintPosition, on_delete=models.CASCADE, verbose_name="Место нанесения принта")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    design_file = models.FileField(upload_to="designs/cart/", verbose_name="Файл макета")
    design_file_2 = models.FileField(upload_to="designs/cart/", null=True, blank=True, verbose_name="Второй макет (например, сзади)")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"

    @property
    def total_price(self):
        return (self.product.price + self.print_position.extra_price) * self.quantity

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Новый'),
        ('WAITING_PAYMENT', 'Ожидает оплаты'),
        ('RECEIPT_PENDING', 'Чек отправлен'),
        ('PAID', 'Оплачен'),
        ('IN_PRODUCTION', 'В производстве'),
        ('PRINTED', 'Напечатан'),
        ('PACKED', 'Упакован'),
        ('SHIPPED', 'Отправлен'),
        ('DELIVERED', 'Доставлен'),
        ('COMPLETED', 'Завершен'),
        ('CANCELLED', 'Отменен'),
    ]

    order_number = models.CharField(max_length=50, unique=True, default=generate_order_number, verbose_name="Номер заказа")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="orders", verbose_name="Клиент")
    full_name = models.CharField(max_length=200, verbose_name="ФИО получателя")
    phone = models.CharField(max_length=50, verbose_name="Телефон")
    address = models.TextField(verbose_name="Адрес доставки")
    city = models.CharField(max_length=100, verbose_name="Город")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Итоговая сумма")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='NEW', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ {self.order_number} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                old_status = Order.objects.get(pk=self.pk).status
            except Order.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        if not is_new and old_status != self.status:
            from .tasks import send_telegram_notification_task
            if self.status not in ['WAITING_PAYMENT', 'RECEIPT_PENDING', 'PAID']:
                send_telegram_notification_task.delay('status_changed', self.id)

    def restore_items_to_cart(self):
        import os
        from apps.orders.models import Cart, CartItem
        
        cart, created = Cart.objects.get_or_create(client=self.client)
        for item in self.items.all():
            cart_item = CartItem.objects.create(
                cart=cart,
                product=item.product,
                size=item.size,
                color=item.color,
                print_position=item.print_position,
                quantity=item.quantity,
                comment=item.comment
            )
            if item.design_file:
                try:
                    cart_item.design_file.save(
                        os.path.basename(item.design_file.name),
                        item.design_file.file,
                        save=True
                    )
                except Exception as e:
                    print(f"Error copying design file back to cart: {e}")
            if item.design_file_2:
                try:
                    cart_item.design_file_2.save(
                        os.path.basename(item.design_file_2.name),
                        item.design_file_2.file,
                        save=True
                    )
                except Exception as e:
                    print(f"Error copying second design file back to cart: {e}")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="Товар")
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, verbose_name="Размер")
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, verbose_name="Цвет")
    print_position = models.ForeignKey(PrintPosition, on_delete=models.SET_NULL, null=True, verbose_name="Место нанесения принта")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    design_file = models.FileField(upload_to="designs/orders/", verbose_name="Файл макета")
    design_file_2 = models.FileField(upload_to="designs/orders/", null=True, blank=True, verbose_name="Второй макет (например, сзади)")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    item_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за единицу (с принтом)")


    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"

    @property
    def total_price(self):
        return self.item_price * self.quantity

    def __str__(self):
        return f"{self.product.title if self.product else 'Удаленный товар'} x {self.quantity}"

class PaymentMethod(models.Model):
    title = models.CharField(max_length=100, verbose_name="Название (например, Сбербанк)")
    card_number = models.CharField(max_length=50, verbose_name="Номер карты/счета")
    receiver_name = models.CharField(max_length=200, verbose_name="Имя получателя")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Способ оплаты"
        verbose_name_plural = "Способы оплаты"

    def __str__(self):
        return f"{self.title} - {self.receiver_name}"

class Receipt(models.Model):
    RECEIPT_STATUS = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Подтвержден'),
        ('rejected', 'Отклонен'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="receipts", verbose_name="Заказ")
    image = models.ImageField(upload_to="receipts/", verbose_name="Фото чека")
    status = models.CharField(max_length=20, choices=RECEIPT_STATUS, default='pending', verbose_name="Статус проверки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Загружен")

    class Meta:
        verbose_name = "Чек об оплате"
        verbose_name_plural = "Чеки об оплате"

    def __str__(self):
        return f"Чек для {self.order.order_number} ({self.get_status_display()})"
