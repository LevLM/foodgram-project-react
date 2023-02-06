from django_filters.rest_framework import CharFilter, FilterSet
from recipes.models import Ingredient


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
