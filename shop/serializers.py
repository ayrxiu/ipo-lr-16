from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, Category, Maker, Cart, CartItem, Profile, Order

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'definition']

class MakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maker
        fields = ['id', 'name', 'country', 'definition']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    maker = MakerSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    maker_id = serializers.PrimaryKeyRelatedField(
        queryset=Maker.objects.all(), source='maker', write_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'definition', 'photo', 'price', 'quantity',
            'category', 'category_id', 'maker', 'maker_id'
        ]

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price']

    def get_total_price(self, obj):
        return obj.total_price()

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'items', 'total_price']

    def get_total_price(self, obj):
        return obj.total_price()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    favorite_category_name = serializers.CharField(source='favorite_category.name', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'full_name', 'phone', 'address', 'city',
            'favorite_category', 'favorite_category_name', 'role', 'created_at'
        ]
        read_only_fields = ['user', 'role', 'created_at']

    def update(self, instance, validated_data):
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.address = validated_data.get('address', instance.address)
        instance.city = validated_data.get('city', instance.city)
        instance.favorite_category = validated_data.get('favorite_category', instance.favorite_category)
        instance.save()
        return instance

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'created_at', 'address', 'total_price']