from django.http import Http404
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db import transaction

from apps.users.models import Client, StoreSettings
from apps.products.models import Product
from .models import Cart, CartItem, Order, OrderItem, PaymentMethod, Receipt
from .serializers import (
    CartSerializer, CartItemSerializer, OrderSerializer, 
    PaymentMethodSerializer, ReceiptSerializer, CheckoutSerializer
)
from .tasks import send_telegram_notification_task

class GetCartView(APIView):
    def get(self, request):
        telegram_id = request.query_params.get('telegram_id')
        if not telegram_id:
            return Response({"error": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        client = get_object_or_404(Client, telegram_id=telegram_id)
        cart, created = Cart.objects.get_or_create(client=client)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

class AddToCartView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        if not telegram_id:
            return Response({"error": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        client = get_object_or_404(Client, telegram_id=telegram_id)
        cart, created = Cart.objects.get_or_create(client=client)
        
        # Build cart item data
        product_id = request.data.get('product')
        size_id = request.data.get('size')
        color_id = request.data.get('color')
        print_position_id = request.data.get('print_position')
        quantity = int(request.data.get('quantity', 1))
        design_file = request.FILES.get('design_file')
        comment = request.data.get('comment', '')
        from apps.products.models import PrintPosition
        print_pos = get_object_or_404(PrintPosition, id=print_position_id)
        design_file_2 = request.FILES.get('design_file_2')
        
        # If print position requires multiple layouts, but the user skipped the second one,
        # reuse the first layout image.
        if print_pos.requires_multiple_designs and not design_file_2:
            design_file_2 = design_file

        if not design_file:
            return Response({"error": "design_file is required"}, status=status.HTTP_400_BAD_REQUEST)

        cart_item = CartItem.objects.create(
            cart=cart,
            product_id=product_id,
            size_id=size_id,
            color_id=color_id,
            print_position_id=print_position_id,
            quantity=quantity,
            design_file=design_file,
            design_file_2=design_file_2,
            comment=comment
        )

        serializer = CartItemSerializer(cart_item, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UpdateCartItemView(APIView):
    def post(self, request):
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))
        
        cart_item = get_object_or_404(CartItem, id=item_id)
        if quantity <= 0:
            cart_item.delete()
            return Response({"message": "Item removed"}, status=status.HTTP_200_OK)
        
        cart_item.quantity = quantity
        cart_item.save()
        
        serializer = CartItemSerializer(cart_item, context={'request': request})
        return Response(serializer.data)

class DeleteCartItemView(APIView):
    def delete(self, request, pk):
        cart_item = get_object_or_404(CartItem, pk=pk)
        cart_item.delete()
        return Response({"message": "Item deleted"}, status=status.HTTP_204_NO_CONTENT)

class ClearCartView(APIView):
    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        client = get_object_or_404(Client, telegram_id=telegram_id)
        cart, created = Cart.objects.get_or_create(client=client)
        cart.items.all().delete()
        return Response({"message": "Cart cleared"}, status=status.HTTP_200_OK)

class CheckoutView(APIView):
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        client = get_object_or_404(Client, telegram_id=data['telegram_id'])
        cart = get_object_or_404(Cart, client=client)
        
        cart_items = cart.items.all()
        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        settings = StoreSettings.load()
        
        # Calculate total price
        total_price = sum(item.total_price for item in cart_items)
        if total_price < settings.min_order_amount:
            return Response(
                {"error": f"Minimum order amount is {settings.min_order_amount} {settings.currency}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Create Order
            order = Order.objects.create(
                client=client,
                full_name=data['full_name'],
                phone=data['phone'],
                address=data['address'],
                city=data['city'],
                total_price=total_price,
                status='WAITING_PAYMENT'
            )
            
            # Create Order Items and copy design files
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    size=item.size,
                    color=item.color,
                    print_position=item.print_position,
                    quantity=item.quantity,
                    design_file=item.design_file,  # Django copies the file field reference
                    design_file_2=item.design_file_2,
                    comment=item.comment,          # Copy comment from cart item
                    item_price=item.product.price + item.print_position.extra_price
                )
            
            # Clear Cart
            cart_items.delete()
        
        # Notify admins/managers & client about new order
        send_telegram_notification_task.delay('new_order', order.id)

        return Response(OrderSerializer(order, context={'request': request}).data, status=status.HTTP_201_CREATED)

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        telegram_id = self.request.query_params.get('telegram_id')
        if not telegram_id:
            return Order.objects.none()
        client = get_object_or_404(Client, telegram_id=telegram_id)
        
        if client.is_manager:
            status_param = self.request.query_params.get('status')
            if status_param:
                return Order.objects.filter(status=status_param).order_by('-created_at')
            return Order.objects.all().order_by('-created_at')
            
        return Order.objects.filter(client=client).order_by('-created_at')

class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class PaymentMethodListView(generics.ListAPIView):
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer

class UploadReceiptView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        image = request.FILES.get('image')
        if not image:
            return Response({"error": "image is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        receipt = Receipt.objects.create(
            order=order,
            image=image,
            status='pending'
        )
        
        # Update order status
        order.status = 'RECEIPT_PENDING'
        order.save()
        
        # Notify admins about receipt
        send_telegram_notification_task.delay('new_receipt', order.id, receipt_id=receipt.id)
        
        # Notify client receipt sent
        send_telegram_notification_task.delay('client_receipt_uploaded', order.id)

        return Response(ReceiptSerializer(receipt, context={'request': request}).data, status=status.HTTP_201_CREATED)

class VerifyReceiptView(APIView):
    def post(self, request, pk):
        # Allow verifying receipts (e.g. from admins/managers)
        # In a real environment, you would check request.user.is_staff.
        # For simple bot-admin buttons, we can secure it using admin auth or internal token.
        # Let's check staff/superuser or check if custom secret token matches.
        # We can also secure with standard session/token auth. Let's make it check is_staff.
        # If request is from bot service (signed or checking localhost/bot token), we can also accept.
        # To make it simple and secure, let's accept if request.user is staff or if a bot secret is present.
        token = request.data.get('token')
        action = request.data.get('action') # 'approve' or 'reject'
        
        receipt = get_object_or_404(Receipt, pk=pk)
        order = receipt.order
        
        # Check security: token must match bot token (internal verification request from bot)
        from django.conf import settings
        if token != settings.TELEGRAM_BOT_TOKEN and not (request.user and request.user.is_staff):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        
        if action == 'approve':
            receipt.status = 'approved'
            receipt.save()
            order.status = 'PAID'
            order.save()
            # Notify client payment approved
            send_telegram_notification_task.delay('payment_approved', order.id)
        elif action == 'reject':
            receipt.status = 'rejected'
            receipt.save()
            order.status = 'WAITING_PAYMENT'
            order.save()
            # Restore items to client's cart so they are not lost
            order.restore_items_to_cart()
            # Notify client payment rejected
            comment = request.data.get('comment')
            send_telegram_notification_task.delay('payment_rejected', order.id, comment=comment)
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(OrderSerializer(order, context={'request': request}).data)

from django.db.models import Sum

class ManagerStatsView(APIView):
    def get(self, request):
        telegram_id = request.query_params.get('telegram_id')
        if not telegram_id:
            return Response({"error": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        client = get_object_or_404(Client, telegram_id=telegram_id)
        if not client.is_manager:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
            
        total_orders = Order.objects.count()
        total_clients = Client.objects.count()
        
        # Revenue is sum of paid/completed orders
        revenue = Order.objects.filter(status__in=[
            'PAID', 'IN_PRODUCTION', 'PRINTED', 'PACKED', 'SHIPPED', 'DELIVERED', 'COMPLETED'
        ]).aggregate(total=Sum('total_price'))['total'] or 0.00
        
        new_receipts = Order.objects.filter(status='RECEIPT_PENDING').count()
        in_production = Order.objects.filter(status='IN_PRODUCTION').count()
        
        return Response({
            "total_orders": total_orders,
            "total_clients": total_clients,
            "revenue": float(revenue),
            "new_receipts": new_receipts,
            "in_production": in_production
        })

class CancelOrderView(APIView):
    def post(self, request, pk):
        token = request.data.get('token')
        from django.conf import settings
        if token != settings.TELEGRAM_BOT_TOKEN and not (request.user and request.user.is_staff):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        order = get_object_or_404(Order, pk=pk)
        if order.status in ['CANCELLED', 'DELIVERED', 'COMPLETED']:
            return Response({"error": "Cannot cancel this order"}, status=status.HTTP_400_BAD_REQUEST)
            
        order.restore_items_to_cart()
        order.status = 'CANCELLED'
        order.save()
        
        comment = request.data.get('comment')
        from .tasks import send_telegram_notification_task
        send_telegram_notification_task.delay('status_changed', order.id, comment=comment)
        
        return Response({"status": "order cancelled and items restored"})

class OtherServicesView(APIView):
    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        comment = request.data.get('comment')
        phone = request.data.get('phone')
        
        if not telegram_id or not comment or not phone:
            return Response({"error": "telegram_id, comment, and phone are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        client = get_object_or_404(Client, telegram_id=telegram_id)
        if not client.phone:
            client.phone = phone
            client.save()
            
        from .tasks import send_other_services_notification
        send_other_services_notification(client, comment, phone)
        return Response({"status": "success"})

class UpdateOrderStatusView(APIView):
    def post(self, request, pk):
        token = request.data.get('token')
        from django.conf import settings
        if token != settings.TELEGRAM_BOT_TOKEN and not (request.user and request.user.is_staff):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
            
        status_val = request.data.get('status')
        order = get_object_or_404(Order, pk=pk)
        if status_val not in dict(Order.STATUS_CHOICES):
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
            
        order.status = status_val
        order.save()
        return Response(OrderSerializer(order, context={'request': request}).data)

