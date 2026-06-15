from django.db import models

class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class Client(models.Model):
    telegram_id = models.BigIntegerField(unique=True, db_index=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=150, null=True, blank=True, verbose_name="Имя пользователя Telegram")
    first_name = models.CharField(max_length=150, verbose_name="Имя")
    phone = models.CharField(max_length=50, null=True, blank=True, verbose_name="Телефон")
    language = models.CharField(max_length=10, default='ru', verbose_name="Язык")
    is_manager = models.BooleanField(default=False, verbose_name="Менеджер")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return f"{self.first_name} (@{self.username or 'без юзернейма'})"

class StoreSettings(SingletonModel):
    shop_name = models.CharField(max_length=100, default="Принт Магазин", verbose_name="Название магазина")
    logo = models.ImageField(upload_to="settings/", null=True, blank=True, verbose_name="Логотип")
    contacts = models.TextField(blank=True, verbose_name="Контакты")
    manager_telegram = models.CharField(max_length=100, blank=True, help_text="Например: @manager_username или ссылка", verbose_name="Telegram менеджера")
    currency = models.CharField(max_length=10, default="UZS", verbose_name="Валюта")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Минимальная сумма заказа")
    welcome_text = models.TextField(blank=True, verbose_name="Текст приветствия")
    welcome_text_uz = models.TextField(blank=True, verbose_name="Текст приветствия (UZ)")
    about_text = models.TextField(blank=True, verbose_name="Текст о компании")
    about_text_uz = models.TextField(blank=True, verbose_name="Текст о компании (UZ)")
    admin_chat_id = models.CharField(max_length=50, blank=True, help_text="Telegram ID чата/канала или администратора для отправки уведомлений о заказах и чеках", verbose_name="Telegram ID чата уведомлений")

    class Meta:
        verbose_name = "Настройки магазина"
        verbose_name_plural = "Настройки магазина"

    def __str__(self):
        return self.shop_name
