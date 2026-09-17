from rest_framework import viewsets
from apps.shop.models import Category, Brand, Product, Cart, CartItem, Order
from .serializers import (
    CategorySerializer, BrandSerializer, ProductSerializer,
    CartSerializer, CartItemSerializer, OrderSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from google import genai
import numpy as np

# Qolgan viewset kodlari o'zgarishsiz qoladi...

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({"error": "q parametri kerak"}, status=400)

        products = list(Product.objects.filter(is_active=True))
        if not products:
            return Response([])

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        texts = [f"{p.name} {p.description or ''}" for p in products]
        texts.append(query)

        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=texts
        )
        embeddings = [np.array(e.values) for e in result.embeddings]

        query_vector = embeddings[-1]
        product_vectors = embeddings[:-1]

        def cosine_sim(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        scores = [cosine_sim(query_vector, v) for v in product_vectors]
        ranked = sorted(zip(products, scores), key=lambda x: x[1], reverse=True)
        top_products = [p for p, score in ranked][:10]

        serializer = self.get_serializer(top_products, many=True)
        return Response(serializer.data)

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
