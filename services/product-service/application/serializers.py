from rest_framework import serializers
from domain.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'product_count', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product listing."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    discount_percent = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    stock_quantity = serializers.ReadOnlyField(source='available_stock')

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'compare_price',
            'image_url', 'category_slug', 'category_name', 'brand', 'stock_quantity',
            'sold_count', 'rating_avg', 'rating_count',
            'discount_percent', 'is_in_stock', 'is_active', 'created_at',
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for product detail."""
    category = CategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    discount_percent = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    stock_quantity = serializers.ReadOnlyField(source='available_stock')

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'category', 'category_id',
            'brand', 'price', 'compare_price', 'sku', 'stock_quantity',
            'sold_count', 'specifications', 'image_url', 'images',
            'is_active', 'rating_avg', 'rating_count',
            'discount_percent', 'is_in_stock',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'sold_count', 'rating_avg', 'rating_count', 'created_at', 'updated_at']


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'category', 'brand',
            'price', 'compare_price', 'sku', 'stock_quantity',
            'specifications', 'image_url', 'images', 'is_active',
        ]
