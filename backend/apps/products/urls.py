from django.urls import path
from .views import CategoryListView, ProductListView, ProductDetailView, PrintPositionListView

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('print-positions/', PrintPositionListView.as_view(), name='print-position-list'),
]
