from rest_framework import serializers
from .models import Category, Size, Color, Product, ProductImage, PrintPosition

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'image', 'is_active']

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['id', 'name']

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'name', 'hex_color']

class PrintPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintPosition
        fields = ['id', 'name', 'extra_price', 'image', 'requires_multiple_designs']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'price', 'image', 'category', 'is_active']

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    sizes = SizeSerializer(many=True, read_only=True)
    colors = ColorSerializer(many=True, read_only=True)
    gallery_images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'title', 'description', 'image', 
            'price', 'sizes', 'colors', 'gallery_images', 'is_active', 'created_at'
        ]
