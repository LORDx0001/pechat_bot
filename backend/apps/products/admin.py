from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Size, Color, Product, ProductImage, PrintPosition, PortfolioItem

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_uz', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'name_uz')

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_uz', 'hex_color')
    search_fields = ('name', 'name_uz', 'hex_color')

@admin.register(PrintPosition)
class PrintPositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_uz', 'extra_price', 'image_preview')
    search_fields = ('name', 'name_uz')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" style="border-radius:4px;" />', obj.image.url)
        return "Нет фото"
    image_preview.short_description = "Превью схемы"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_uz', 'category', 'price', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'title_uz', 'description', 'description_uz')
    filter_horizontal = ('sizes', 'colors')
    inlines = [ProductImageInline]

@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_uz', 'image_preview', 'created_at')
    search_fields = ('title', 'title_uz', 'description', 'description_uz')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" style="border-radius:4px;" />', obj.image.url)
        return "Нет фото"
    image_preview.short_description = "Фото готового изделия"
