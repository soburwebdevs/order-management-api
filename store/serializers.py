from django.db import transaction
from rest_framework import serializers
from store import models


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=models.Category.objects.all()
    )
    discounted_price = serializers.SerializerMethodField()
    
    def get_discounted_price(self, product: models.Product):
        promotions = product.promotion.all()
        if not promotions.exists():
            return product.unit_price
        
        best_discount = max(promo.discount for promo in promotions)
        return product.unit_price * (1 - best_discount / 100)
    
    class Meta:
        model = models.Product
        fields = ['id', 'title', 'slug', 'description', 'unit_price', 'discounted_price', 'stock', 'category', 'last_update']


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = ['id', 'title', 'unit_price']


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    def get_total_price(self, cart_item: models.CartItem):
        return cart_item.quantity * cart_item.product.unit_price
    
    class Meta:
        model = models.CartItem
        fields = ['id', 'product', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    
    def get_total_price(self, cart: models.Cart):
        return sum([item.quantity * item.product.unit_price for item in cart.items.all()])
    
    class Meta:
        model = models.Cart
        fields = ['id', 'created_at', 'items', 'total_price']


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()
    
    def validate_product_id(self, value):
        if not models.Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('No product with the given ID was found.')
        return value
    
    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']
        
        try:
            cart_item = models.CartItem.objects.get(cart_id=cart_id, product_id=product_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except models.CartItem.DoesNotExist:
            self.instance = models.CartItem.objects.create(cart_id=cart_id, **self.validated_data)
        
        return self.instance
    
    class Meta:
        model = models.CartItem
        fields = ['id', 'product_id', 'quantity']


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    
    class Meta:
        model = models.OrderItem
        fields = ['id', 'product', 'unit_price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = models.Order
        fields = ['id', 'user', 'status', 'placed_at', 'items']


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()
    
    def validate_cart_id(self, cart_id):
        if not models.Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('No Cart found with the given ID.')
        if models.CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError('The cart is empty.')
        return cart_id
    
    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            user_id = self.context['user_id']
            
            order = models.Order.objects.create(user_id=user_id)
            
            cart_items = models.CartItem.objects.select_related('product').filter(cart_id=cart_id)
            order_items = [
                models.OrderItem(
                    order=order,
                    product=item.product,
                    unit_price=item.product.unit_price,
                    quantity=item.quantity
                ) for item in cart_items
            ]
            models.OrderItem.objects.bulk_create(order_items)
            
            models.Cart.objects.filter(pk=cart_id).delete()
            
            self.instance = order
            return order
        
    def to_representation(self, instance):
        return OrderSerializer(instance).data


