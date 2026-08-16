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
    
    class Meta:
        model = models.Product
        fields = ['id', 'title', 'slug', 'description', 'unit_price', 'stock', 'category', 'last_update']


