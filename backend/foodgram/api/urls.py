from django.urls import include, path
from djoser.views import TokenDestroyView, UserViewSet
from rest_framework import routers

from .views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                    TokenCreateView, UserRecipeViewSet)

# app_name = 'api'

router = routers.DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
    path(r'auth/token/login/', TokenCreateView.as_view(), name='login'),
    path(r'auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
    path(r'users/', UserViewSet.as_view(
        {'get': 'list', 'post': 'create'}), name='users'),
    path(r'users/<int:id>/', UserViewSet.as_view(
        {'get': 'retrieve'}), name='user-detail'),
    path(r'users/me/', UserViewSet.as_view({'get': 'me'}), name='me-detail'),
    path(
        r'users/set_password/',
        UserViewSet.as_view({'post': 'set_password'}),
        name='set-password',
    ),
    path(
        r'users/subscriptions/',
        UserRecipeViewSet.as_view({'get': 'list'}),
        name='subscriptions',
    ),
    path(
        r'users/<int:author_id>/subscribe/',
        UserRecipeViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
        name='subscribe',
    ),
]
