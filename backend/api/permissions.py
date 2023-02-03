from django.core.handlers.wsgi import WSGIRequest
from rest_framework.permissions import DjangoModelPermissions  # noqa F401
from rest_framework.permissions import IsAuthenticated  # noqa F401
from rest_framework.permissions import (BasePermission,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.routers import APIRootView
from users.models import MyUser


class AuthorStaffOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешение на изменение только для служебного персонала и автора.
    Остальным только чтение объекта.
    """
    def has_object_permission(
        self,
        request: WSGIRequest,
        view: APIRootView,
        obj: MyUser
    ) -> bool:
        return (
            request.method == 'GET'
            or request.user.is_authenticated
            and request.user.active
            and (
                request.user == obj.author
                or request.user.is_staff
            )
        )


class AdminOrReadOnly(BasePermission):
    """
    Разрешение на создание и изменение только для админов.
    Остальным только чтение объекта.
    """
    def has_permission(
        self,
        request: WSGIRequest,
        view: APIRootView
    ) -> bool:
        return (
            request.method == 'GET'
            or (
                request.user.is_authenticated
                and request.user.active
                and request.user.is_admin
            )
        )


class OwnerUserOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешение на изменение только для админа и пользователя.
    Остальным только чтение объекта.
    """
    def has_object_permission(
        self,
        request: WSGIRequest,
        view: APIRootView,
        obj: MyUser
    ) -> bool:
        return (
            request.method == 'GET'
            or (
                request.user.is_authenticated
                and request.user.active
                and (
                    request.user == obj
                    or request.user.is_admin
                )
            )
        )
