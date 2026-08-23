from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from store import views

router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='category')
router.register('products', views.ProductViewSet, basename='product')
router.register('carts', views.CartViewSet, basename='cart')

carts_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
carts_router.register('items', views.CartItemViewSet, basename='cart-items')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(carts_router.urls)),
]
