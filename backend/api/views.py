from datetime import datetime as dt
from urllib.parse import unquote

from api.mixins import AddDelViewMixin
from api.paginators import PageLimitPagination
from api.permissions import (AdminOrReadOnly, AuthorStaffOrReadOnly,
                             DjangoModelPermissions, IsAuthenticated)
from api.serializers import (IngredientSerializer, RecipeSerializer,
                             ShortRecipeSerializer, TagSerializer,
                             UserSubscribeSerializer)
from core.enums import Tuples, UrlQueries
from core.services import incorrect_layout
from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import F, QuerySet, Sum
from django.db.models.manager import BaseManager
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from foodgram.settings import DATE_TIME_FORMAT
from recipes.models import (AmountIngredient, Cart, Favorite, Ingredient,
                            Recipe, Tag)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from users.models import MyUser

User: MyUser = get_user_model()


class BaseAPIRootView(APIRootView):
    """Базовые пути API приложения.
    """


class UserViewSet(DjoserUserViewSet, AddDelViewMixin):
    """Работает с пользователями.

    ViewSet для работы с пользователми - вывод таковых,
    регистрация.
    Для авторизованных пользователей —
    возможность подписаться на автора рецепта.
    """
    pagination_class = PageLimitPagination
    add_serializer = UserSubscribeSerializer
    permission_classes = (DjangoModelPermissions,)

    @action(
        methods=Tuples.ACTION_METHODS,
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request: WSGIRequest, id: int) -> Response:
        """Создаёт/удалет связь между пользователями.

        Вызов метода через url: */user/<int:id>/subscribe/.

        Args:
            request (WSGIRequest): Не используется.
            id (int):
                id пользователя, на которого желает подписаться
                или отписаться запрашивающий пользователь.

        Returns:
            Responce: Статус подтверждающий/отклоняющий действие.
        """
        user = self.request.user
        author = get_object_or_404(self.queryset, id=id)
        serializer: UserSubscribeSerializer = self.add_serializer(
            author, context={'request': self.request}
        )
        subscribe_exist: bool = user.subscribe.filter(id=id).exists()

        if (self.request.method in Tuples.ADD_METHODS) and not subscribe_exist:
            user.subscribe.add(author)
            return Response(serializer.data, status=HTTP_201_CREATED)

        if (self.request.method in Tuples.DEL_METHODS) and subscribe_exist:
            user.subscribe.remove(author)
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_400_BAD_REQUEST)

    @action(methods=('get',), detail=False)
    def subscriptions(self, request: WSGIRequest) -> Response:
        """Список подписок пользоваетеля.

        Вызов метода через url: */user/<int:id>/subscribtions/.

        Args:
            request (WSGIRequest): Не используется.

        Returns:
            Responce:
                401 - для неавторизованного пользователя.
                Список подписок для авторизованного пользователя.
        """
        user = self.request.user
        if user.is_anonymous:
            return Response(status=HTTP_401_UNAUTHORIZED)
        authors: BaseManager[MyUser] = user.subscribe.all()
        pages = self.paginate_queryset(authors)
        serializer = UserSubscribeSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    """Работает с тэгами.

    Изменение и создание тэгов разрешено только админам.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Работет с игридиентами.

    Изменение и создание ингридиентов разрешено только админам.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrReadOnly,)

    def get_queryset(self) -> list[Ingredient]:
        """Получает queryset в соответствии с параметрами запроса.

        Реализован поиск объектов по совпадению в начале названия,
        также добавляются результаты по совпадению в середине.
        При наборе названия в неправильной раскладке - латинские символы
        преобразуются в кириллицу (для стандартной раскладки).
        Также прописные буквы преобразуются в строчные,
        так как все ингридиенты в базе записаны в нижнем регистре.

        Returns:
            list[Ingredient]: Список запрошенных объектов.
        """
        name: str = self.request.query_params.get(UrlQueries.SEARCH_ING_NAME)
        queryset = self.queryset
        if name:
            if name[0] == '%':
                name = unquote(name)
            else:
                name = name.translate(incorrect_layout)
            name = name.lower()
            start_queryset = list(queryset.filter(name__istartswith=name))
            ingridients_set = set(start_queryset)
            cont_queryset = queryset.filter(name__icontains=name)
            start_queryset.extend(
                [ing for ing in cont_queryset if ing not in ingridients_set]
            )
            queryset = start_queryset
        return queryset


class RecipeViewSet(ModelViewSet, AddDelViewMixin):
    """Работает с рецептами.

    Вывод, создание, редактирование, добавление/удаление
    в избранное и список покупок.
    Отправка текстового файла со списком покупок.
    Для авторизованных пользователей — возможность добавить
    рецепт в избранное и в список покупок.
    Изменять рецепт может только автор или админы.
    """
    queryset = Recipe.objects.select_related('author')
    serializer_class = RecipeSerializer
    permission_classes = (AuthorStaffOrReadOnly,)
    pagination_class = PageLimitPagination
    add_serializer = ShortRecipeSerializer

    def get_queryset(self) -> QuerySet[Recipe]:
        """Получает queryset в соответствии с параметрами запроса.

        Returns:
            QuerySet[Recipe]: Список запрошенных объектов.
        """
        queryset = self.queryset

        tags: list = self.request.query_params.getlist(UrlQueries.TAGS.value)
        if tags:
            queryset = queryset.filter(
                tags__slug__in=tags).distinct()

        author: str = self.request.query_params.get(UrlQueries.AUTHOR.value)
        if author:
            queryset = queryset.filter(author=author)

        # Следующие фильтры только для авторизованного пользователя
        if self.request.user.is_anonymous:
            return queryset

        is_in_cart: str = self.request.query_params.get(UrlQueries.SHOP_CART)
        if is_in_cart in Tuples.SYMBOL_TRUE_SEARCH.value:
            queryset = queryset.filter(cart__user=self.request.user)
        elif is_in_cart in Tuples.SYMBOL_FALSE_SEARCH.value:
            queryset = queryset.exclude(cart__user=self.request.user)

        is_favorit: str = self.request.query_params.get(UrlQueries.FAVORITE)
        if is_favorit in Tuples.SYMBOL_TRUE_SEARCH.value:
            queryset = queryset.filter(favorite__user=self.request.user)
        if is_favorit in Tuples.SYMBOL_FALSE_SEARCH.value:
            queryset = queryset.exclude(favorite__user=self.request.user)
        return queryset

    @action(
        methods=Tuples.ACTION_METHODS,
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request: WSGIRequest, pk: int) -> Response:
        """Добавляет/удалет рецепт в `избранное`.

        Вызов метода через url: */recipe/<int:pk>/favorite/.

        Args:
            request (WSGIRequest): Не используется.
            pk (int):
                id рецепта, который нужно добавить/удалить из `избранного`.

        Returns:
            Responce: Статус подтверждающий/отклоняющий действие.
        """
        return self.add_del_obj(pk, Favorite)

    @action(
        methods=Tuples.ACTION_METHODS,
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request: WSGIRequest, pk: int) -> Response:
        """Добавляет/удалет рецепт в `список покупок`.

        Вызов метода через url: *//recipe/<int:pk>/shopping_cart/.

        Args:
            request (WSGIRequest): Не используется.
            pk (int):
                id рецепта, который нужно добавить/удалить в `корзину покупок`.

        Returns:
            Responce: Статус подтверждающий/отклоняющий действие.
        """
        return self.add_del_obj(pk, Cart)

    @action(methods=('get',), detail=False)
    def download_shopping_cart(self, request: WSGIRequest) -> Response:
        """Загружает файл *.txt со списком покупок.

        Считает сумму ингредиентов в рецептах выбранных для покупки.
        Возвращает текстовый файл со списком ингредиентов.
        Вызов метода через url:  */recipe/<int:id>/download_shopping_cart/.

        Args:
            request (WSGIRequest): Не используется.

        Returns:
            Responce: Ответ с текстовым файлом.
        """
        user = self.request.user
        if not user.carts.exists():
            return Response(status=HTTP_400_BAD_REQUEST)
        ingredients = AmountIngredient.objects.filter(
            recipe__in=(user.carts.values('id'))
        ).values(
            ingredient=F('ingredients__name'),
            measure=F('ingredients__measurement_unit')
        ).annotate(amount=Sum('amount'))

        filename = f'{user.username}_shopping_list.txt'
        shopping_list = (
            f'Список покупок для:\n\n{user.first_name}\n\n'
            f'{dt.now().strftime(DATE_TIME_FORMAT)}\n\n'
        )
        for ing in ingredients:
            shopping_list += (
                f'{ing["ingredient"]}: {ing["amount"]} {ing["measure"]}\n'
            )

        shopping_list += '\n\nПосчитано в Foodgram'

        response = HttpResponse(
            shopping_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
