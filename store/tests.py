from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase
from decimal import Decimal
from store import models

User = get_user_model()


class CartCreationTestCase(APITestCase):
    def test_create_cart_success(self):
        response = self.client.post(reverse('cart-list'), {})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['items'], [])
        self.assertEqual(response.data['total_price'], 0)
    
    def test_cart_uses_unique_id(self):
        mycart = self.client.post(reverse('cart-list'), {})
        mycartid = mycart.data['id']
        
        yourcart = self.client.post(reverse('cart-list'), {})
        yourcartid = yourcart.data['id']
        
        self.assertNotEqual(mycartid, yourcartid)


class CartItemTestCase(APITestCase):
    def setUp(self):
        self.category = models.Category.objects.create(name="Electronics")
        self.product = models.Product.objects.create(
            title="Table Fan",
            slug="table-fan",
            unit_price=40.99,
            stock=10,
            category=self.category
        )
        self.cart = models.Cart.objects.create()
        
    def test_add_item_to_cart(self):
        url = reverse('cart-items-list', kwargs={'cart_pk': self.cart.id})
        data = {'product_id': self.product.id, 'quantity': 2}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_add_same_product_merges_quantity(self):
        url = reverse('cart-items-list', kwargs={'cart_pk': self.cart.id})
        
        self.client.post(url, {'product_id': self.product.id, 'quantity': 2})
        self.client.post(url, {'product_id': self.product.id, 'quantity': 3})
        
        self.assertEqual(models.CartItem.objects.count(), 1)
        
        cart_item = models.CartItem.objects.get(cart=self.cart, product=self.product)
        self.assertEqual(cart_item.quantity, 5)
    
    def test_add_nonexistent_product_fails(self):
        url = reverse('cart-items-list', kwargs={'cart_pk': self.cart.id})
        response = self.client.post(url, {'product_id': 9999, 'quantity': 1})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_update_cart_item_quantity(self):
        url = reverse('cart-items-list', kwargs={'cart_pk': self.cart.id})
        response = self.client.post(url, {'product_id': self.product.id, 'quantity': 2})
        item_id = response.data['id']
        
        detail_url = reverse('cart-items-detail', kwargs={'cart_pk': self.cart.id, 'pk': item_id})
        response = self.client.patch(detail_url, {'quantity': 5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 5)
    
    def test_delete_cart_item(self):
        url = reverse('cart-items-list', kwargs={'cart_pk': self.cart.id})
        response = self.client.post(url, {'product_id': self.product.id, 'quantity': 1})
        item_id = response.data['id']
        
        detail_url = reverse('cart-items-detail', kwargs={'cart_pk': self.cart.id, 'pk': item_id})
        response = self.client.delete(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.CartItem.objects.count(), 0)
        
    def test_cart_total_price_calculation(self):
        url = reverse('cart-items-list', kwargs={'cart_pk': self.cart.id})
        response = self.client.post(url, {'product_id': self.product.id, 'quantity': 3})
        
        cart_url = reverse('cart-detail', kwargs={'pk': self.cart.id})
        response = self.client.get(cart_url)
        
        expected_total = self.product.unit_price * 3
        self.assertEqual(float(response.data['total_price']), float(expected_total))


class CheckoutTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@test.com",
            password="TestPass@123"
        )
        self.category = models.Category.objects.create(name="Electronics")
        self.product = models.Product.objects.create(
            title="Table Fan",
            slug="table-fan",
            unit_price=40.99,
            stock=10,
            category=self.category
        )
        self.cart = models.Cart.objects.create(user=self.user)
        self.cart_item = models.CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
        self.client.force_authenticate(user=self.user)
    
    def test_checkout_success(self):
        response = self.client.post(reverse('order-list'), {'cart_id': self.cart.id})
        
        order = models.Order.objects.first()
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.Order.objects.count(), 1)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.items.count(), 1)
    
    def test_checkout_freezes_unit_price(self):
        self.client.post(reverse('order-list'), {'cart_id': self.cart.id})
        order = models.Order.objects.first()
        
        self.product.unit_price = 999.99
        self.product.save()
        
        order_item = order.items.first()
        order_item.refresh_from_db()
        
        self.assertEqual(order_item.unit_price, Decimal('40.99'))
    
    def test_checkout_empty_cart_fails(self):
        self.cart_item.delete()
        response = self.client.post(reverse('order-list'), {'cart_id': self.cart.id})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(models.Order.objects.count(), 0)
        
    def test_checkout_transaction_rollback(self):
        with patch.object(models.OrderItem.objects, 'bulk_create', side_effect=Exception("DB crashed")):
            try:
                self.client.post(reverse('order-list'), {'cart_id': self.cart.id})
            except Exception:
                pass
        
        self.assertEqual(models.Order.objects.count(), 0)
        self.assertEqual(models.CartItem.objects.count(), 1)
        self.assertTrue(models.Cart.objects.filter(pk=self.cart.id).exists())
    
    def test_checkout_sends_confirmation_email(self):
        self.client.post(reverse('order-list'), {'cart_id': self.cart.id})
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])


class ProductDiscountTestCase(APITestCase):
    def setUp(self):
        self.category = models.Category.objects.create(name="Electronics")
        self.product = models.Product.objects.create(
            title="Table Fan",
            slug="table-fan",
            unit_price=100,
            stock=10,
            category=self.category
        )
        
    def test_discounted_price_no_promotion(self):
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        response = self.client.get(url)
        
        self.assertEqual(response.data['discounted_price'], Decimal('100'))
    
    def test_discounted_price_with_single_promotion(self):
        promo = models.Promotion.objects.create(description="Winter Sale", discount=20)
        self.product.promotion.add(promo)
        
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        response = self.client.get(url)
        
        self.assertEqual(response.data['discounted_price'], Decimal('80'))
    
    def test_discounted_price_picks_best_discount(self):
        promo1 = models.Promotion.objects.create(description="Summer Sale", discount=20)
        promo2 = models.Promotion.objects.create(description="Winter Sale", discount=30)
        promo3 = models.Promotion.objects.create(description="A Sale", discount=10)
        
        self.product.promotion.add(promo1, promo2, promo3)
        
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        response = self.client.get(url)
        
        self.assertEqual(response.data['discounted_price'], Decimal('70'))


class ProductTestCase(APITestCase):
    def setUp(self):
        self.category = models.Category.objects.create(name="Electronics")
        self.product = models.Product.objects.create(
            title="Table Fan",
            slug="table-fan",
            unit_price=40.99,
            stock=10,
            category=self.category
        )
        
    def test_list_products(self):
        response = self.client.get(reverse('product-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_retrieve_single_product(self):
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.product.id)
        self.assertEqual(response.data['title'], 'Table Fan')
        
    def test_category_show_as_name_not_id(self):
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        response = self.client.get(url)
        
        self.assertEqual(response.data['category'], 'Electronics')

