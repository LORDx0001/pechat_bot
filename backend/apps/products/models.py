from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    name_uz = models.CharField(max_length=100, null=True, blank=True, verbose_name="Название (UZ)")
    image = models.ImageField(upload_to="categories/", null=True, blank=True, verbose_name="Изображение")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Размер")

    class Meta:
        verbose_name = "Размер"
        verbose_name_plural = "Размеры"

    def __str__(self):
        return self.name

class Color(models.Model):
    name = models.CharField(max_length=100, verbose_name="Цвет")
    name_uz = models.CharField(max_length=100, null=True, blank=True, verbose_name="Цвет (UZ)")
    hex_color = models.CharField(max_length=7, default="#FFFFFF", help_text="HEX код, например #FFFFFF", verbose_name="HEX код цвета")

    class Meta:
        verbose_name = "Цвет"
        verbose_name_plural = "Цвета"

    def __str__(self):
        return f"{self.name} ({self.hex_color})"

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="Категория")
    title = models.CharField(max_length=200, verbose_name="Название")
    title_uz = models.CharField(max_length=200, null=True, blank=True, verbose_name="Название (UZ)")
    description = models.TextField(verbose_name="Описание")
    description_uz = models.TextField(null=True, blank=True, verbose_name="Описание (UZ)")
    image = models.ImageField(upload_to="products/", verbose_name="Основное изображение")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    sizes = models.ManyToManyField(Size, related_name="products", verbose_name="Доступные размеры")
    colors = models.ManyToManyField(Color, related_name="products", verbose_name="Доступные цвета")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery_images", verbose_name="Товар")
    image = models.ImageField(upload_to="products/gallery/", verbose_name="Изображение")

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товара"

class PrintPosition(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название места")
    name_uz = models.CharField(max_length=100, null=True, blank=True, verbose_name="Название места (UZ)")
    extra_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Дополнительная стоимость")
    image = models.ImageField(upload_to="print_positions/", null=True, blank=True, verbose_name="Изображение-схема")
    requires_multiple_designs = models.BooleanField(default=False, verbose_name="Требует два макета (например, спереди и сзади)")


    class Meta:
        verbose_name = "Место нанесения принта"
        verbose_name_plural = "Места нанесения принтов"

    def __str__(self):
        return f"{self.name} (+{self.extra_price})"

class PortfolioItem(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    title_uz = models.CharField(max_length=200, blank=True, null=True, verbose_name="Название (UZ)")
    description = models.TextField(blank=True, verbose_name="Описание")
    description_uz = models.TextField(blank=True, null=True, verbose_name="Описание (UZ)")
    image = models.ImageField(upload_to="portfolio/", verbose_name="Фото готового изделия")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Готовое изделие (Портфолио)"
        verbose_name_plural = "Готовые изделия (Портфолио)"

    def __str__(self):
        return self.title
