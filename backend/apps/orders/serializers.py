from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, PaymentMethod, Receipt
from apps.products.serializers import ProductListSerializer, SizeSerializer, ColorSerializer, PrintPositionSerializer
from apps.users.serializers import ClientSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductListSerializer(source='product', read_only=True)
    size_details = SizeSerializer(source='size', read_only=True)
    color_details = ColorSerializer(source='color', read_only=True)
    print_position_details = PrintPositionSerializer(source='print_position', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_details', 'size', 'size_details', 
            'color', 'color_details', 'print_position', 'print_position_details', 
            'quantity', 'design_file', 'design_file_2', 'comment', 'total_price'
        ]

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_cart_price = serializers.SerializerMethodField()
    client_details = ClientSerializer(source='client', read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'client', 'client_details', 'items', 'total_cart_price', 'created_at']

    def get_total_cart_price(self, obj):
        return sum(item.total_price for item in obj.items.all())

class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductListSerializer(source='product', read_only=True)
    size_details = SizeSerializer(source='size', read_only=True)
    color_details = ColorSerializer(source='color', read_only=True)
    print_position_details = PrintPositionSerializer(source='print_position', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_details', 'size', 'size_details', 
            'color', 'color_details', 'print_position', 'print_position_details', 
            'quantity', 'design_file', 'design_file_2', 'comment', 'item_price', 'total_price'
        ]

class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ['id', 'order', 'image', 'status', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    receipts = ReceiptSerializer(many=True, read_only=True)
    client_details = ClientSerializer(source='client', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'client', 'client_details', 'full_name', 
            'phone', 'address', 'city', 'total_price', 'status', 'status_display',
            'items', 'receipts', 'created_at'
        ]

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'title', 'card_number', 'receiver_name', 'is_active']

class CheckoutSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    full_name = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=50)
    address = serializers.CharField()
    city = serializers.CharField(max_length=100)
