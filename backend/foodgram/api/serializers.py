import base64
import uuid

from django.core.files.base import ContentFile
# from django.shortcuts import get_object_or_404
from recipes.models import (Favorite, Follow, Ingredient, IngredientNumber,
                            Recipe, ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
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
        fields = ('id', 'name', 'color', 'slug')


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
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed',
        )


class IngredientNumberSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(source='number')

    class Meta:
        model = IngredientNumber
        fields = ('id', 'name', 'measurement_unit', 'amount')


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
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    image = Base64ImageField(
        allow_null=True
    )
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientNumberSerializer(
        source='ingredient_number',
        many=True
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

    # def validate(self, data):
    #     ingredients = data['ingredient_number']
    #     if len(ingredients) != len(
    #         set(obj['ingredient'] for obj in ingredients)
    #     ):
    #         raise serializers.ValidationError(
    #             'Ingredients should be unique')
    #     if any(obj['number'] <= 0 for obj in ingredients):
    #         raise serializers.ValidationError(
    #             'Number of Ingredient should be > 0'
    #         )
    #     return super().validate(data)

        # ingredients_set = set()
        # for ingredient in ingredients:
        #     if int(ingredient.get('number')) <= 0:
        #         raise serializers.ValidationError(
        #             ('Number of Ingredient should be > 0')
        #         )
        #     id = ingredient.get('id')
        #     if len(ingredients) > len(set(ingredients)):
        #         if id in ingredients_set:
        #             raise serializers.ValidationError(
        #                 'Ingredient is already in Recipe'
        #             )
        #         ingredients_set.add(id)
        # data['ingredients'] = ingredients
        # return data

    # def create(self, validated_data):
    #     image = validated_data.pop('image')
    #     # ingredients = self.initial_data.get('ingredients')
    #     recipe = Recipe.objects.create(image=image, **validated_data)
    #     # # tagsdata = validated_data.tags.get_queryset()
    #     # tags = self.initial_data.get('tags')
    #     # # tags = []
    #     # # for i in tagsdata:
    #     # #     tags.append(i)
    #     # for tag_id in tags:
    #     #     recipe.tags.add(get_object_or_404(Tag, pk=tag_id))
    #     # for ingredient in ingredients:
    #     #     IngredientNumber.objects.bulk_create(
    #     #         recipe=recipe,
    #     #         ingredient_id=ingredient.get('id'),
    #     #         number=ingredient.get('number')
    #     #     )
    #     return recipe

    # def create(self, validated_data):
    #     # ingredients = validated_data.pop('ingredient_number')
    #     tags = validated_data.pop('tags')
    #     recipe = Recipe.objects.create(**validated_data)
    #     # for ingredient in ingredients:
    #        curr_ingredient, status = IngredientNumber.objects.get_or_create(
    #     #         **ingredient)
    #     #     IngredientNumber.objects.create(
    #     #         ingredient=curr_ingredient, recipe=recipe)
    #     for tag in tags:
    #         current_tag, status = Tag.objects.get_or_create(
    #             **tag)
    #         TagRecipe.objects.create(
    #             tag=current_tag, recipe=recipe)
    #     return recipe

    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data, author=author)
        for tag in tags:
            # current_tag, status = Tag.objects.get_or_create(
            #     **tag)
            current_tag = Tag.objects.get_or_create(tag)
            recipe.tags.add(current_tag)
            # TagRecipe.objects.create(
            #     tag=current_tag, recipe=recipe)
        self.save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        instance.text = validated_data.get('text')
        instance.cooking_time = validated_data.get('cooking_time')
        instance.image = validated_data.get('image')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.add(*tags)
        ingredients = validated_data.pop('ingredients_number')
        instance.ingredients.clear()
        recipe = instance
        self.save_ingredients(recipe, ingredients)
        instance.save()
        return instance
