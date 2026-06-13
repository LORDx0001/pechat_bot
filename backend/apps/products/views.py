from rest_framework import generics
from .models import Category, Product, PrintPosition
from .serializers import CategorySerializer, ProductListSerializer, ProductDetailSerializer, PrintPositionSerializer

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer

class ProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer

class PrintPositionListView(generics.ListAPIView):
    queryset = PrintPosition.objects.all()
    serializer_class = PrintPositionSerializer
