"""Модуль вспомогательных функций.
"""
from string import hexdigits

from recipes.models import AmountIngredient, Recipe
from rest_framework.serializers import ValidationError


def recipe_amount_ingredients_set(
    recipe: Recipe,
    ingredients: list[dict]
) -> None:
    """Записывает ингредиенты вложенные в рецепт.

    Создаёт объект AmountIngredient связывающий объекты Recipe и
    Ingredient с указанием количества(`amount`) конкретного ингридиента.

    Args:
        recipe (Recipe):
            Рецепт, в который нужно добавить игридиенты.
        ingridients (list[dict]):
            Список ингридентов и количества сих.
    """
    for ingredient in ingredients:
        AmountIngredient.objects.get_or_create(
            recipe=recipe,
            ingredients=ingredient['ingredient'],
            amount=ingredient['amount']
        )


def is_hex_color(value: str) -> None:
    """Проверяет - может ли значение быть шестнадцатеричным цветом.

    Args:
        value (str):
            Значение переданное для проверки.

    Raises:
        ValidationError:
            Переданное значение не корректной длины.
        ValidationError:
            Символы значения выходят за пределы 16-ричной системы.
    """
    if len(value) not in (3, 6):
        raise ValidationError(
            f'{value} не правильной длины ({len(value)}).'
        )
    if not set(value).issubset(hexdigits):
        raise ValidationError(
            f'{value} не шестнадцатиричное.'
        )


# Словарь для сопостановления латинской и русской стандартных раскладок.
incorrect_layout = str.maketrans(
    'qwertyuiop[]asdfghjkl;\'zxcvbnm,./',
    'йцукенгшщзхъфывапролджэячсмитьбю.'
)
