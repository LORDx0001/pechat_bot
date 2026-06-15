from django.urls import path
from .views import (
    GetCartView, AddToCartView, UpdateCartItemView, DeleteCartItemView, ClearCartView,
    CheckoutView, OrderListView, OrderDetailView, PaymentMethodListView, UploadReceiptView,
    VerifyReceiptView, ManagerStatsView, CancelOrderView, OtherServicesView, UpdateOrderStatusView
)

urlpatterns = [
    # Cart urls
    path('cart/', GetCartView.as_view(), name='cart-get'),
    path('cart/add/', AddToCartView.as_view(), name='cart-add'),
    path('cart/update/', UpdateCartItemView.as_view(), name='cart-update'),
    path('cart/items/<int:pk>/', DeleteCartItemView.as_view(), name='cart-delete-item'),
    path('cart/clear/', ClearCartView.as_view(), name='cart-clear'),
    
    # Checkout & Orders
    path('orders/checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/other-services/', OtherServicesView.as_view(), name='other-services'),
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/upload-receipt/', UploadReceiptView.as_view(), name='order-upload-receipt'),
    path('orders/<int:pk>/cancel/', CancelOrderView.as_view(), name='order-cancel'),
    path('orders/<int:pk>/status/', UpdateOrderStatusView.as_view(), name='order-status-update'),
    
    # Payment methods
    path('payment-methods/', PaymentMethodListView.as_view(), name='payment-methods-list'),
    
    # Verification
    path('receipts/<int:pk>/verify/', VerifyReceiptView.as_view(), name='receipt-verify'),
    
    # Manager stats
    path('manager/stats/', ManagerStatsView.as_view(), name='manager-stats'),
]
