from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, RetrieveModelMixin)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from recipes.models import (Favorite, Follow, Ingredient, IngredientNumber,
                            Recipe, ShoppingCart, Tag)
from users.models import User

from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientNumberSerializer, IngredientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          TagSerializer, UserSerializer)


class CreateListDestroyViewSet(
    CreateModelMixin, DestroyModelMixin,
    ListModelMixin, RetrieveModelMixin, GenericViewSet):
    pass


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend,)
    pagination_class = LimitOffsetPagination
    serializer_class = RecipeSerializer
    filterset_fields = ('author', 'tags') 

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, ],
        filter_backends = (DjangoFilterBackend,),
        filterset_fields = ('tags',) 
    )
    def favorite(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
            serializer = FavoriteSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                instance, created = Favorite.objects.get_or_create(user=user, recipe=recipe)
                if not created:
                    serializer.update(instance, serializer.validated_data)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        if not Favorite.objects.filter(user=user,
                                       recipe=recipe).exists():
            return Response({'error, Favorite not found'},
                            status=status.HTTP_404_NOT_FOUND)
        Favorite.objects.get(recipe=recipe).delete()
        return Response('Recipe deleted from Favorite',
                        status=status.HTTP_204_NO_CONTENT)


    @action(detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, ]
    )
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                instance, created = ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
                if not created:
                    serializer.update(instance, serializer.validated_data)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        if not ShoppingCart.objects.filter(user=user,
                                           recipe=recipe).exists():
            return Response({'error, ShoppingCart not found'},
                            status=status.HTTP_404_NOT_FOUND)
        ShoppingCart.objects.get(recipe=recipe).delete()
        return Response('Recipe deleted from ShoppingCart',
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = user.shopping_cart.all()
        shopping_list = {}
        for i in shopping_cart:
            recipe = i.recipe
            ingredients = IngredientNumber.objects.filter(recipe=recipe)
            for ingredient in ingredients:
                number = ingredient.number
                name = ingredient.ingredient.name
                measurement_unit = ingredient.ingredient.measurement_unit
                if name not in shopping_list:
                    shopping_list[name] = {
                        'measurement_unit': measurement_unit,
                        'number': number
                    }
                else:
                    shopping_list[name]['number'] = (
                        shopping_list[name]['number'] + number
                    )
        shopping_list_print = []
        for idx, elem in enumerate(shopping_list, start=1):
            shopping_list_print.append(
                idx, '.',
                elem, ' (',
                shopping_list[i]['measurement_unit'], ') - ',
                shopping_list[i]['number'], '\n'
            )
        response = HttpResponse(shopping_list_print, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="shoplist.txt"'
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    search_fields = ('^name',)


class RecipeIngredientViewSet(viewsets.ModelViewSet):
    queryset = IngredientNumber.objects.all()
    serializer_class = IngredientNumberSerializer


class TagViewSet(CreateListDestroyViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class FollowViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet
                    ):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('=user__username', '=following__username')

    def get_queryset(self):
        user = self.request.user
        return user.follower.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    lookup_field = 'username'

    @action(
        detail=False,
        methods=(['GET', 'PATCH']),
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        serializer = UserSerializer(
            request.user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role)
        return Response(serializer.data)
