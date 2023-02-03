"""Модуль содержит дополнительные классы
для настройки основных классов приложения.
"""
from core.enums import Tuples
from django.db.models import Model
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST)


class AddDelViewMixin:
    """
    Добавляет во Viewset дополнительные методы.

    Содержит метод добавляющий/удаляющий объект связи
    Many-to-Many между моделями.
    Требует определения атрибута `add_serializer`.

    Example:
        class ExampleViewSet(ModelViewSet, AddDelViewMixin)
            ...
            add_serializer = ExamplSerializer

            def example_func(self, request, **kwargs):
                ...
                obj_id = ...
                return self.add_del_obj(obj_id, relation.M2M)
    """

    add_serializer: ModelSerializer | None = None

    def add_del_obj(
        self,
        recipe_id: int,
        m2m_model: Model
    ) -> Response:
        """Добавляет/удаляет связи M2M между пользователеми и рецептами.

        Args:
            recipe_id (int):
                id рецепта, с которым требуется создать/удалить связь.
            m2m_model (Model):
                М2M модель управляющая требуемой связью.

        Returns:
            Responce: Статус подтверждающий/отклоняющий действие.
        """
        user = self.request.user
        recipe = get_object_or_404(self.queryset, id=recipe_id)
        serializer: ModelSerializer = self.add_serializer(
            recipe, context={'request': self.request}
        )
        m2m_instance = m2m_model.objects.filter(recipe=recipe, user=user)

        if (self.request.method in Tuples.ADD_METHODS) and not m2m_instance:
            m2m_model(recipe=recipe, user=user).save()
            return Response(serializer.data, status=HTTP_201_CREATED)
        if (self.request.method in Tuples.DEL_METHODS) and m2m_instance:
            m2m_instance[0].delete()
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_400_BAD_REQUEST)
