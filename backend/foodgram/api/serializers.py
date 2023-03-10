import base64
import uuid

from django.core.files.base import ContentFile
from djoser import serializers as djoser_serializers
from recipes.models import (Favorite, Follow, Ingredient, IngredientNumber,
                            Recipe, ShoppingCart, Tag)
from rest_framework import serializers
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


class RecipeMiniOutputSerializer(serializers.ModelSerializer):
    image = Base64ImageField(use_url=True, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = fields


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Follow
        fields = (
            'user',
            'author',
        )

    def validate(self, data):
        user = self.context.get('request').user
        author = self.initial_data.get('author')
        if user == author:
            raise serializers.ValidationError('???????????? ?????????????????????? ???? ????????')
        if author.follower.filter(user=user).exists():
            raise serializers.ValidationError(
                '???????????? ?????????????????????? ?????????? 1 ???????? ???? ???????????? ????????????????????????'
            )
        return super().validate(data)


class UserSerializer(djoser_serializers.UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, author):
        request = self.context['request']
        return (
            request.user.is_authenticated
            and author.follower.filter(user=request.user).exists()
        )

    class Meta(djoser_serializers.UserSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed',
        )


class UserRecipeSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )
        read_only_fields = fields

    def get_recipes(self, user_object):
        queryset = user_object.recipes.all()
        return RecipeMiniOutputSerializer(queryset, many=True).data

    def get_recipes_count(self, user_object):
        return user_object.recipes.count()


class IngredientNumberSerializer(serializers.ModelSerializer):
    id = serializers.SlugRelatedField(
        source='ingredient',
        slug_field='id',
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(source='number')

    class Meta:
        model = IngredientNumber
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        read_only_fields = ('user', 'recipe')

    def to_representation(self, instance):
        return RecipeMiniOutputSerializer(instance, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        read_only_fields = ('user', 'recipe')

    def to_representation(self, instance):
        return RecipeMiniOutputSerializer(instance, context=self.context).data


class RecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('tags', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    image = Base64ImageField(
        allow_null=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    ingredients = IngredientNumberSerializer(
        source='ingredient_number',
        many=True
    )

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data

    def validate(self, data):
        if len(data['tags']) == 0:
            raise serializers.ValidationError(
                '???????????? ???????? ?????????????? ???? ?????????? 1 ????????'
            )
        if len(data['tags']) != len(set(data['tags'])):
            raise serializers.ValidationError(
                '???????????? ???????????????? ???????? ?? ?????? ???? ??????'
            )
        if len(data['ingredient_number']) == 0:
            raise serializers.ValidationError(
                '???????????? ???????? ?????????????? ???? ?????????? 1 ??????????????????????'
            )
        ingredients = data['ingredient_number']
        if len(ingredients) != len(
                set(obj['ingredient'] for obj in ingredients)):
            raise serializers.ValidationError(
                '???????????? ???????????????? ???????? ?? ?????? ???? ????????????????????')
        if any(obj['number'] <= 0 for obj in ingredients):
            raise serializers.ValidationError(
                '???????????????????? ???????????????????? ???????????? ???????? ???????????? ????????'
            )
        if data['cooking_time'] <= 0:
            raise serializers.ValidationError(
                '?????????? ?????????????????????????? ???????????? ???????? ???????????? ????????'
            )
        return super().validate(data)

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            IngredientNumber.objects.create(
                recipe=recipe,
                number=ingredient.get('number'),
                ingredient=ingredient.get('ingredient')
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredient_number')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, recipe, validated_data):
        if 'ingredient_number' in validated_data:
            ingredient_number = validated_data.pop('ingredient_number')
            if 'ingredient_number':
                recipe.ingredients.clear()
            RecipeSerializer.create_ingredients(
                self, ingredient_number, recipe
            )
        return super().update(recipe, validated_data)


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(
        default=serializers.CurrentUserDefault(),
    )
    image = Base64ImageField(use_url=True)
    ingredients = IngredientNumberSerializer(
        source='ingredient_number', many=True,
    )
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'tags', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_ingredients(self, obj):
        return IngredientNumberSerializer(
            IngredientNumber.objects.filter(recipe=obj), many=True).data

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
