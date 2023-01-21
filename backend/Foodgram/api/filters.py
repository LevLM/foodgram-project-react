from django_filters.rest_framework import FilterSet, filters

from recipes.models import Recipe, Tag
from users.models import User


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(
        method='get_is_favorited'
    )

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'tags']

    def get_is_favorited(self, queryset, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite_recipe_user=user)
        return queryset
