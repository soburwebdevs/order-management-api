from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Promotion


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'unit_price', 'stock', 'last_update')
    list_filter = ('category',)
    prepopulated_fields = {'slug': ('title',)}
    

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    inlines = [CartItemInline]


class OrderItemInine(admin.TabularInline):
    model = OrderItem
    extra = 0
    

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'placed_at')
    list_filter = ('status',)
    inlines = [OrderItemInine]
    

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('description', 'discount')
