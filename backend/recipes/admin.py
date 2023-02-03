from django.contrib.admin import ModelAdmin, TabularInline, register, site
from django.core.handlers.wsgi import WSGIRequest
from django.utils.safestring import SafeString, mark_safe
from recipes.models import (AmountIngredient, Cart, Favorite, Ingredient,
                            Recipe, Tag)

site.site_header = 'Администрирование Foodgram'
EMPTY_VALUE_DISPLAY = 'Значение не указано'


class IngredientInline(TabularInline):
    model = AmountIngredient
    extra = 2


@register(AmountIngredient)
class LinksAdmin(ModelAdmin):
    pass


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = (
        'name', 'measurement_unit',
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'name',
    )

    save_on_top = True
    empty_value_display = EMPTY_VALUE_DISPLAY


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = (
        'name', 'author', 'get_image', 'count_favorites',
    )
    fields = (
        ('name', 'cooking_time',),
        ('author', 'tags',),
        ('text',),
        ('image',),
    )
    raw_id_fields = ('author', )
    search_fields = (
        'name', 'author__username', 'tags__name',
    )
    list_filter = (
        'name', 'author__username', 'tags__name'
    )

    inlines = (IngredientInline,)
    save_on_top = True
    empty_value_display = EMPTY_VALUE_DISPLAY

    def get_image(self, obj: Recipe) -> SafeString:
        return mark_safe(f'<img src={obj.image.url} width="80" hieght="30"')

    get_image.short_description = 'Изображение'

    def count_favorites(self, obj: Recipe) -> int:
        return obj.favorite.count()

    count_favorites.short_description = 'В избранном'


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = (
        'name', 'color', 'slug',
    )
    search_fields = (
        'name', 'color'
    )

    save_on_top = True
    empty_value_display = EMPTY_VALUE_DISPLAY


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = (
        'user', 'recipe', 'date_added'
    )
    search_fields = (
        'user__username', 'recipe__name'
    )

    def has_change_permission(
        self,
        request: WSGIRequest,
        obj: Favorite | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self,
        request: WSGIRequest,
        obj: Favorite | None = None
    ) -> bool:
        return False


@register(Cart)
class CardAdmin(ModelAdmin):
    list_display = (
        'user', 'recipe', 'date_added'
    )
    search_fields = (
        'user__username', 'recipe__name'
    )

    def has_change_permission(
        self,
        request: WSGIRequest,
        obj: Cart | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self,
        request: WSGIRequest,
        obj: Cart | None = None
    ) -> bool:
        return False
