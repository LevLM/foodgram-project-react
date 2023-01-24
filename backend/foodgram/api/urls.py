from django.urls import include, path
from rest_framework import routers

from .views import (FollowViewSet, IngredientViewSet, RecipeViewSet,
                    TagViewSet, UserViewSet)

router = routers.DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register('subscriptions', FollowViewSet, basename='follow')
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
