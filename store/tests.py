from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
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
    
