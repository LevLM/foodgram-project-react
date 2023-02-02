from django.db.models.query_utils import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views
from recipes.models import (Favorite, Follow, Ingredient, IngredientNumber,
                            Recipe, ShoppingCart, Tag)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, RetrieveModelMixin)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from users.models import User
from users.permissions import IsAuthorOrReadOnly

from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipeListSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          TagSerializer, UserRecipeSerializer)


class CreateListDestroyViewSet(
        CreateModelMixin, DestroyModelMixin,
        ListModelMixin, RetrieveModelMixin, GenericViewSet):
    pass


class TokenCreateView(views.TokenCreateView):
    def _action(self, serializer):
        response = super()._action(serializer)
        if response.status_code == status.HTTP_200_OK:
            response.status_code = status.HTTP_201_CREATED
        return response


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    edit_permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = LimitOffsetPagination
    filterset_fields = ('author', 'tags')
    serializer_class = RecipeListSerializer
    edit_serializer_class = RecipeSerializer

    def get_permissions(self):
        if self.action in (
            "destroy",
            "partial_update",
        ):
            return [
                permission() for permission in self.edit_permission_classes]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in (
            "create",
            "partial_update",
        ):
            return self.edit_serializer_class
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user
        is_favorited = self.request.query_params.get("is_favorited")
        if is_favorited:
            recipes_id = (
                Favorite.objects.filter(user=user).values("recipe__id")
                if user.is_authenticated
                else []
            )
            condition = Q(id__in=recipes_id)
            queryset = queryset.filter(
                condition if is_favorited == "1" else ~condition
            ).all()
        is_in_shopping_cart = self.request.query_params.get(
            "is_in_shopping_cart")
        if is_in_shopping_cart:
            recipes_id = (
                ShoppingCart.objects.filter(user=user).values("recipe__id")
                if user.is_authenticated
                else []
            )
            condition = Q(id__in=recipes_id)
            queryset = queryset.filter(
                condition if is_in_shopping_cart == "1" else ~condition
            ).all()
        author_id = self.request.query_params.get("author")
        if author_id:
            queryset = queryset.filter(author__id=author_id).all()

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ]
            )
    def favorite(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
            serializer = FavoriteSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                instance, created = Favorite.objects.get_or_create(
                    user=user, recipe=recipe)
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
    def shopping_cart(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                instance, created = ShoppingCart.objects.get_or_create(
                    user=user, recipe=recipe)
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
        response = HttpResponse(shopping_list_print,
                                'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="shoplist.txt"'
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    search_fields = ('^name',)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    pagination_class = None

    def get_queryset(self):
        return Tag.objects.all()


class UserRecipeViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserRecipeSerializer
    permission_classes = (IsAuthenticated,)

    def get_author(self) -> User:
        return get_object_or_404(User, id=self.kwargs.get('author_id'))

    def get_object(self):
        return get_object_or_404(
            Follow, user=self.request.user, author=self.get_author()
        )

    def destroy(self, request, *args, **kwargs):
        self.get_author()
        try:
            self.get_object()
        except Http404:
            data = {'errors': 'Нельзя отменить подписку, если не был подписан'}
            return JsonResponse(data, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action in (
            'create',
            'destroy',
        ):
            return FollowSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return User.objects.filter(follower__user=self.request.user)
        return None

    def create(self, request, *args, **kwargs):
        request.data.update(author=self.get_author())
        super().create(request, *args, **kwargs)
        serializer = self.serializer_class(
            instance=self.get_author(), context=self.get_serializer_context()
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        serializer.save(author=self.get_author())
