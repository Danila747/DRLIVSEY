"""Модуль для создания, настройки и управления моделью пользователей.

Задаёт модели и методы для настроийки и управления пользователями
приложения `Foodgram`. Модель пользователя основана на модели
AbstractUser из Django для переопределения полей обязательных для заполнения.
"""
from core import texsts
from core.enums import Limits
from django.contrib.auth.models import AbstractUser
from django.db.models import (BooleanField, CharField, CheckConstraint, CASCADE, DateTimeField, UniqueConstraint,
                              EmailField, ManyToManyField, Q, Model, ForeignKey, F)
from django.db.models.functions import Length
from django.utils.translation import gettext_lazy as _
from users.validators import MinLenValidator, OneOfTwoValidator

CharField.register_lookup(Length)


class MyUser(AbstractUser):
    """Настроенная под приложение `Foodgram` модель пользователя.

    При создании пользователя все поля обязательны для заполнения.

    Attributes:
        email(str):
            Адрес email пользователя.
            Проверка формата производится внутри Django.
            Установлено ограничение по максимальной длине.
        username(str):
            Юзернейм пользователя.
            Установлены ограничения по минимальной и максимальной длине.
            Для ввода разрешены только буквы.
        first_name(str):
            Реальное имя пользователя.
            Установлено ограничение по максимальной длине.
        last_name(str):
            Реальная фамилия пользователя.
            Установлено ограничение по максимальной длине.
        password(str):
            Пароль для авторизации.
            Внутри Django проходит хэш-функцию с добавлением
            `соли` settings.SECRET_KEY.
            Хранится в зашифрованном виде.
            Установлено ограничение по максимальной длине.
        active (bool):
            Активен или заблокирован пользователь.
        subscribe(int):
            Ссылки на id связанных пользователей.
    """
    email = EmailField(
        verbose_name='Адрес электронной почты',
        max_length=Limits.MAX_LEN_EMAIL_FIELD.value,
        unique=True,
        help_text=texsts.USERS_HELP_EMAIL
    )
    username = CharField(
        verbose_name='Уникальный юзернейм',
        max_length=Limits.MAX_LEN_USERS_CHARFIELD.value,
        unique=True,
        help_text=(texsts.USERS_HELP_UNAME),
        validators=(
            MinLenValidator(min_len=Limits.MIN_LEN_USERNAME),
            OneOfTwoValidator(),
        ),
    )
    first_name = CharField(
        verbose_name='Имя',
        max_length=Limits.MAX_LEN_USERS_CHARFIELD.value,
        help_text=texsts.USERS_HELP_FNAME
    )
    last_name = CharField(
        verbose_name='Фамилия',
        max_length=Limits.MAX_LEN_USERS_CHARFIELD.value,
        help_text=texsts.USERS_HELP_FNAME
    )
    password = CharField(
        verbose_name=_('Пароль'),
        max_length=Limits.MAX_LEN_USERS_CHARFIELD.value,
        help_text=texsts.USERS_HELP_FNAME
    )
    active = BooleanField(
        verbose_name=' Активирован',
        default=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)
        constraints = (
            CheckConstraint(
                check=Q(username__length__gte=Limits.MIN_LEN_USERNAME.value),
                name='\nusername too short\n',
            ),
        )

    def __str__(self) -> str:
        return f'{self.username}: {self.email}'


class Subscriptions(Model):
    """Подписки пользователей друг на друга.

    Attributes:
        author(int):
            Автор рецепта. Связь через ForeignKey.
        user(int):
            Подписчик Связь через ForeignKey.
        date_added(datetime):
            Дата создания подписки.
    """
    author = ForeignKey(
        verbose_name='Автор рецепта',
        related_name='subscribers',
        to=MyUser,
        on_delete=CASCADE,
    )
    user = ForeignKey(
        verbose_name='Подписчики',
        related_name='subscriptions',
        to=MyUser,
        on_delete=CASCADE,
    )
    date_added = DateTimeField(
        verbose_name='Дата создания подписки',
        auto_now_add=True,
        editable=False
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            UniqueConstraint(
                fields=('author', 'user'),
                name='\nRepeat subscription\n',
            ),
            CheckConstraint(
                check=~Q(author=F('user')),
                name='\nNo self sibscription\n'
            )
        )

    def __str__(self) -> str:
        return f'{self.user.username} -> {self.author.username}'
