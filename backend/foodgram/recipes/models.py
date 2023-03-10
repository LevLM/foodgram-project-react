from django.core import validators
from django.db import models
from users.models import User


class Ingredient(models.Model):
    name = models.CharField(max_length=200, blank=False)
    measurement_unit = models.CharField(
        max_length=10,
        blank=False,
        verbose_name='ед.измерения'
    )

    class Meta:
        ordering = ['-name']
        constraints = [models.UniqueConstraint(
            fields=['name', 'measurement_unit'],
            name='unique_ingredient')
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, unique=True, blank=False)
    COLOR_CHOICES = (
        ('#0505ff', 'blue'),
        ('#ddff03', 'yellow'),
        ('#738678', 'grey'),
        ('#ff0000', 'red'),
    )
    color = models.TextField(
        choices=COLOR_CHOICES, unique=True,
        blank=False, null=True, max_length=7
    )
    slug = models.SlugField(
        unique=True, blank=False, null=True, max_length=200
    )

    class Meta:
        ordering = ['-name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes', blank=False)
    name = models.CharField(max_length=200, blank=False)
    image = models.ImageField(
        upload_to='recipes/', null=True,
        blank=False
    )
    text = models.TextField(blank=False)
    ingredients = models.ManyToManyField(
        Ingredient,
        blank=False,
        through='IngredientNumber',
    )
    tags = models.ManyToManyField(Tag, blank=False)
    cooking_time = models.PositiveIntegerField(
        blank=False,
        validators=(
            validators.MaxValueValidator(3000),
            validators.MinValueValidator(1),
        )
    )

    class Meta:
        verbose_name = 'Recipe'

    def __str__(self):
        return self.name


class UserFollow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        abstract = True


class Follow(UserFollow):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='unique_follow',
                fields=['user', 'author'],
            ),
        ]

    def __str__(self):
        return self.author


class IngredientNumber(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_number'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_number'
    )
    number = models.PositiveIntegerField(
        blank=False,
        validators=(
            validators.MaxValueValidator(999),
            validators.MinValueValidator(1),
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'],
                                    name='ingredient_number')
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_favorite')
        ]

    def __str__(self):
        return f'Рецепт {self.recipe} в списке Избранное у {self.user}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_shopping_cart')
        ]
