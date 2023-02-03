"""Модуль для создания, настройки и управления моделями пакета `recipe`.

Models:
    Recipe:
        Основная модель приложения, через которую описываются рецепты.
    Tag:
       Модель для группировки рецептов по тэгам.
       Связана с Recipe через Many-To-Many.
    Ingredient:
        Модель для описания ингредиентов.
        Связана с Recipe через модель AmountIngredient (Many-To-Many).
    AmountIngredient:
        Модель для связи Ingredient и Recipe.
        Также указывает количество ингридиента.
    Favorite:
        Указывает избранные пользователем рецепты.
    Cart:
        Рецепты в корзине покупок пользователя.
"""
from core.enums import Limits, Tuples
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (CASCADE, CharField, CheckConstraint,
                              DateTimeField, ForeignKey, ImageField,
                              ManyToManyField, Model,
                              PositiveSmallIntegerField, Q, TextField,
                              UniqueConstraint)
from django.db.models.functions import Length
from PIL import Image
from users.models import MyUser

CharField.register_lookup(Length)

User: MyUser = get_user_model()


class Tag(Model):
    """Тэги для рецептов.

    Связано с моделью Recipe через М2М.
    Поля `name` и 'slug` - обязательны для заполнения.

    Attributes:
        name(str):
            Название тэга. Установлены ограничения по длине и уникальности.
        color(str):
            Цвет тэга в HEX-кодировке. По умолчанию - чёрный
        slug(str):
            Те же правила, что и для атрибута `name`, но для корректной работы
            с фронтэндом следует заполнять латинскими буквами.

    Example:
        Tag('Завтрак', '01AB89', 'breakfirst')
        Tag('Завтрак', '01AB89', 'zavtrak')
    """
    name = CharField(
        verbose_name='Тэг',
        max_length=Limits.MAX_LEN_RECIPES_CHARFIELD.value,
        unique=True,
        null=False,
    )
    color = CharField(
        verbose_name='Цветовой HEX-код',
        max_length=6,
        unique=True,
        null=False,
    )
    slug = CharField(
        verbose_name='Слаг тэга',
        max_length=Limits.MAX_LEN_RECIPES_CHARFIELD.value,
        unique=True,
        null=False
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name', )

    def __str__(self) -> str:
        return f'{self.name} (цвет: {self.color})'

    def save(self, *args, **kwargs) -> None:
        self.name = self.name.lower()
        self.color = self.color.upper()
        self.slug = self.slug.lower()
        super().save(*args, **kwargs)


class Ingredient(Model):
    """Ингридиенты для рецепта.

    Связано с моделью Recipe через М2М (AmountIngredient).

    Attributes:
        name(str):
            Название ингридиента.
            Установлены ограничения по длине и уникальности.
        measurement_unit(str):
            Единицы измерения ингридентов (граммы, штуки, литры и т.п.).
            Установлены ограничения по длине.
    """
    name = CharField(
        verbose_name='Ингридиент',
        max_length=Limits.MAX_LEN_RECIPES_CHARFIELD.value,
    )
    measurement_unit = CharField(
        verbose_name='Единицы измерения',
        max_length=Limits.MAX_LEN_MEASUREMENT.value,
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('name', )
        constraints = (
            UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_for_ingredient'
            ),
            CheckConstraint(
                check=Q(name__length__gt=0),
                name='\n%(app_label)s_%(class)s_name is empty\n',
            ),
            CheckConstraint(
                check=Q(measurement_unit__length__gt=0),
                name='\n%(app_label)s_%(class)s_measurement_unit is empty\n',
            ),
        )

    def __str__(self) -> str:
        return f'{self.name} {self.measurement_unit}'

    def save(self, *args, **kwargs) -> None:
        self.name = self.name.lower()
        self.measurement_unit = self.measurement_unit.lower()
        super().save(*args, **kwargs)


class Recipe(Model):
    """Модель для рецептов.

    Основная модель приложения описывающая рецепты.

    Attributes:
        name(str):
            Название рецепта. Установлены ограничения по длине.
        author(int):
            Автор рецепта. Связан с моделю User через ForeignKey.
        favorite(int):
            Связь M2M с моделью User.
            Создаётся при добавлении пользователем рецепта в `избранное`.
        tags(int):
            Связь M2M с моделью Tag.
        ingredients(int):
            Связь M2M с моделью Ingredient. Связь создаётся посредством модели
            AmountIngredient с указанием количества ингридиента.
        cart(int):
            Связь M2M с моделью User.
            Создаётся при добавлении пользователем рецепта в `покупки`.
        pub_date(datetime):
            Дата добавления рецепта. Прописывается автоматически.
        image(str):
            Изображение рецепта. Указывает путь к изображению.
        text(str):
            Описание рецепта. Установлены ограничения по длине.
        cooking_time(int):
            Время приготовления рецепта.
            Установлены ограничения по максимальным и минимальным значениям.
    """
    name = CharField(
        verbose_name='Название блюда',
        max_length=Limits.MAX_LEN_RECIPES_CHARFIELD.value,
    )
    author = ForeignKey(
        verbose_name='Автор рецепта',
        related_name='recipes',
        to=User,
        on_delete=CASCADE,
    )
    tags = ManyToManyField(
        verbose_name='Тег',
        related_name='recipes',
        to='Tag',
    )
    ingredients = ManyToManyField(
        verbose_name='Ингредиенты блюда',
        related_name='recipes',
        to=Ingredient,
        through='recipes.AmountIngredient',
    )
    pub_date = DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    image = ImageField(
        verbose_name='Изображение блюда',
        upload_to='recipe_images/',
    )
    text = TextField(
        verbose_name='Описание блюда',
        max_length=Limits.MAX_LEN_RECIPES_TEXTFIELD.value,
    )
    cooking_time = PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        default=0,
        validators=(
            MinValueValidator(
                Limits.MIN_COOKING_TIME.value,
                'Ваше блюдо уже готово!'
            ),
            MaxValueValidator(
                Limits.MAX_COOKING_TIME.value,
                'Очень долго ждать...'
            ),
        ),
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )
        constraints = (
            UniqueConstraint(
                fields=('name', 'author'),
                name='unique_for_author'
            ),
            CheckConstraint(
                check=Q(name__length__gt=0),
                name='\n%(app_label)s_%(class)s_name is empty\n',
            ),
        )

    def __str__(self) -> str:
        return f'{self.name}. Автор: {self.author.username}'

    def save(self, *args, **kwargs) -> None:
        self.name = self.name.capitalize()
        super().save(*args, **kwargs)
        image = Image.open(self.image.path)
        image = image.resize(Tuples.RECIPE_IMAGE_SIZE)
        image.save(self.image.path)


class AmountIngredient(Model):
    """Количество ингридиентов в блюде.

    Модель связывает Recipe и Ingredient с указанием количества ингридиента.

    Attributes:
        recipe(int):
            Связаный рецепт. Связь через ForeignKey.
        ingredients(int):
            Связаный ингридиент. Связь через ForeignKey.
        amount(int):
            Количиства ингридиента в рецепте. Установлены ограничения
            по минимальному и максимальному значениям.
    """
    recipe = ForeignKey(
        verbose_name='В каких рецептах',
        related_name='ingredient',
        to=Recipe,
        on_delete=CASCADE,
    )
    ingredients = ForeignKey(
        verbose_name='Связанные ингредиенты',
        related_name='recipe',
        to=Ingredient,
        on_delete=CASCADE,
    )
    amount = PositiveSmallIntegerField(
        verbose_name='Количество',
        default=0,
        validators=(
            MinValueValidator(
                Limits.MIN_AMOUNT_INGREDIENTS,
                'Нужно хоть какое-то количество.'
            ),
            MaxValueValidator(
                Limits.MAX_AMOUNT_INGREDIENTS,
                'Слишком много!'
            ),
        ),
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Количество ингридиентов'
        ordering = ('recipe', )
        constraints = (
            UniqueConstraint(
                fields=('recipe', 'ingredients', ),
                name='\n%(app_label)s_%(class)s ingredient alredy added\n',
            ),
        )

    def __str__(self) -> str:
        return f'{self.amount} {self.ingredients}'


class Favorite(Model):
    """Избранные рецепты.

    Модель связывает Recipe и  User.

    Attributes:
        recipe(int):
            Связаный рецепт. Связь через ForeignKey.
        user(int):
            Связаный пользователь. Связь через ForeignKey.
        date_added (datetime):
            Дата длбавления рецепта в избранное.
    """
    recipe = ForeignKey(
        verbose_name='Понравившиеся рецепты',
        related_name='favorite',
        to=Recipe,
        on_delete=CASCADE,
    )
    user = ForeignKey(
        verbose_name='Пользователь',
        related_name='favorites',
        to=User,
        on_delete=CASCADE,
    )
    date_added = DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True,
        editable=False
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = (
            UniqueConstraint(
                fields=('recipe', 'user', ),
                name='\n%(app_label)s_%(class)s recipe is favorite alredy\n',
            ),
        )

    def __str__(self) -> str:
        return f'{self.user} -> {self.recipe}'


class Cart(Model):
    """Рецепты в корзине покупок.

    Модель связывает Recipe и  User.

    Attributes:
        recipe(int):
            Связаный рецепт. Связь через ForeignKey.
        user(int):
            Связаный пользователь. Связь через ForeignKey.
        date_added (datetime):
            Дата длбавления рецепта в корзину.
    """
    recipe = ForeignKey(
        verbose_name='Рецепты в списке покупок',
        related_name='cart',
        to=Recipe,
        on_delete=CASCADE,
    )
    user = ForeignKey(
        verbose_name='Владелец списка',
        related_name='carts',
        to=User,
        on_delete=CASCADE,
    )
    date_added = DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True,
        editable=False
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = (
            UniqueConstraint(
                fields=('recipe', 'user', ),
                name='\n%(app_label)s_%(class)s recipe is cart alredy\n',
            ),
        )

    def __str__(self) -> str:
        return f'{self.user} -> {self.recipe}'
