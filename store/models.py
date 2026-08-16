from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    stock = models.PositiveIntegerField()
    last_update = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    
    def __str__(self):
        return self.title


