from rest_framework import viewsets, permissions
from .models import Category, Brand, Product, Cart, Order, Review
from .serializers import (
    CategorySerializer, BrandSerializer, ProductSerializer,
    CartSerializer, OrderSerializer, ReviewSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ Kategoriya ro'yxati va amallari """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class BrandViewSet(viewsets.ModelViewSet):
    """ Brendlar ro'yxati """
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.AllowAny]


class ProductViewSet(viewsets.ModelViewSet):
    """ Mahsulotlarni korish, qidirish va filtrlash """
    queryset = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images')
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]


class CartViewSet(viewsets.ModelViewSet):
    """ Foydalanuvchi savatchasi """
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Faqat o'ziga tegishli savatchani ko'rish uchun
        return Cart.objects.filter(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    """ Buyurtmalar ro'yxati va yaratish """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Faqat o'z buyurtmalarini ko'rsatish
        return Order.objects.filter(user=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    """ Mahsulotlarga yozilgan sharhlar """
    queryset = Review.objects.filter(is_published=True)
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]