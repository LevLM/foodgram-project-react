from django_filters import ModelMultipleChoiceFilter
from django_filters.rest_framework import FilterSet
from recipes.models import Recipe, Tag


class TagRecipeFilter(FilterSet):

    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )

    class Meta:
        model = Recipe
        fields = ('tags',)
