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
        ('#738678', "grey"),
        ('#ff0000', 'red'),
    )
    color = serializers.ChoiceField(choices=COLOR_CHOICES)

    class Meta:
        fields = '__all__'
        model = Tag


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    following = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    def validate_following(self, following):
        if self.context['request'].user == following:
            raise serializers.ValidationError(
                {'following': 'Нельзя подписаться на самого себя'}
            )
        return following

    class Meta:
        fields = ('user', 'following')
        model = Follow
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'following']
            )
        ]


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return Follow.objects.filter(following=obj, user=user).exists()

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

    def validate(self, data):
        if Favorite.objects.filter(
                user=self.context.get('request').user,
                recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError({
                'status': 'Already in Favorite'
            })
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ShoppingCart
        fields = '__all__'

    def validate(self, data):
        if ShoppingCart.objects.filter(
                user=self.context['request'].user,
                recipe=data['recipe']
        ):
            raise serializers.ValidationError('Already in ShoppingCart')
        return data


class RecipeSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = '__all__'
        model = Recipe

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
        ingredient = set()
        for i in ingredients:
            number = int(i.get('number'))
            if number <= 0:
                raise serializers.ValidationError(
                    ('Number of ingredient have to be > 0')
                )
            id = ingredient.get('id')
            if id in ingredient:
                raise serializers.ValidationError(
                    'Ingredient is not unique'
                )
            ingredient.add(id)
        data['ingredients'] = ingredients
        return data

    def create(self, validated_data):
        image = validated_data.pop('image')
        ingredients = validated_data.pop('ingredients')
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
        for ingredient in validated_data.get('ingredients'):
            ingredient_number = IngredientNumber.objects.bulk_create(
                recipe=instance,
                ingredient_id=ingredient.get('id'),
                number=ingredient.get('number')
            )
            ingredient_number.save()
        instance.save()
        return instance
