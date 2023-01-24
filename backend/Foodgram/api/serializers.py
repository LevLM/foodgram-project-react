import base64
import uuid

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Follow, Ingredient, IngredientNumber,
                            Recipe, ShoppingCart, Tag)
from users.models import User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            id = uuid.uuid4()
            data = ContentFile(
                base64.b64decode(imgstr),
                name=id.urn[9:] + '.' + ext)
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    COLOR_CHOICES = (
        ('#0505ff', 'blue'),
        ('#ddff03', 'yellow'),
        ('#738678', 'grey'),
        ('#ff0000', 'red'),
    )
    color = serializers.ChoiceField(choices=COLOR_CHOICES)

    class Meta:
        model = Tag
        fields = '__all__'


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    def validate_following(self, author):
        if self.context['request'].user == author:
            raise serializers.ValidationError(
                {'author': 'Нельзя подписаться на самого себя'}
            )
        return author

    class Meta:
        fields = ('user', 'author')
        model = Follow
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'author']
            )
        ]


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return Follow.objects.filter(author=obj, user=user).exists()

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'password',
            'is_subscribed',
        )


class IngredientNumberSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientNumber
        fields = ('id', 'name', 'measurement_unit', 'number')
        validators = [
            UniqueTogetherValidator(
                queryset=IngredientNumber.objects.all(),
                fields=['ingredient', 'recipe']
            )
        ]


class FavoriteSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Favorite
        fields = '__all__'

 
class ShoppingCartSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ShoppingCart
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'name', 'text',
                  'image', 'ingredients', 'cooking_time',
                  'is_favorited', 'is_in_shopping_cart')

    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientNumberSerializer(
        many=True, read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user,
            recipe=obj
        ).exists()

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredients_set = set()
        for ingredient in ingredients:
            if int(ingredient.get('number')) <= 0:
                raise serializers.ValidationError(
                    ('Number of Ingredient should be > 0')
                )
            id = ingredient.get('id')
            if len(ingredients) > len(set(ingredients)):
                if id in ingredients_set:
                    raise serializers.ValidationError(
                        'Ingredient is already in Recipe'
                    )
                ingredients_set.add(id)
        data['ingredients'] = ingredients
        return data

    def create(self, validated_data):
        image = validated_data.pop('image')
        ingredients = self.initial_data.get('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        tags = self.initial_data.get('tags')
        for tag_id in tags:
            recipe.tags.add(get_object_or_404(Tag, pk=tag_id))
        for ingredient in ingredients:
            IngredientNumber.objects.bulk_create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                number=ingredient.get('number')
            )
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        instance.text = validated_data.get('text')
        instance.cooking_time = validated_data.get('cooking_time')
        instance.image = validated_data.get('image')
        instance.tags.clear()
        tags = self.initial_data.get('tags')
        for tag_id in tags:
            instance.tags.add(get_object_or_404(Tag, pk=tag_id))
        IngredientNumber.objects.filter(recipe=instance).delete()
        instance.ingredients.clear()
        instance.ingredients = self.initial_data.get('ingredients')
        for ingredient in instance.ingredients:
            ingredient_number = IngredientNumber.objects.bulk_create(
                recipe=instance,
                ingredient_id=ingredient.get('id'),
                number=ingredient.get('number')
            )
            ingredient_number.save()
        instance.save()
        return instance
