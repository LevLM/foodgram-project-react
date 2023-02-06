from django_filters.rest_framework import CharFilter, FilterSet
from recipes.models import Tag


class TagFilter(FilterSet):
    name = CharFilter(field_name='name')

    class Meta:
        model = Tag
        fields = ('name',)
