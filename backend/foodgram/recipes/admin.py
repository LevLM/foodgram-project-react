from django.contrib import admin

from .models import Ingredient, Recipe, Tag, IngredientNumber


class RecipeIngredientInline(admin.TabularInline):
    model = IngredientNumber
    fields = ('ingredient', 'number')
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author') 
    list_filter = ('author', 'name', 'tags')
    inlines = (RecipeIngredientInline, )

    def favorite(self, obj):
        return obj.favorites.count()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit') 
    list_filter = ('name',)
    inlines = (RecipeIngredientInline, )


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color') 


admin.site.register(Recipe, RecipeAdmin, ) 
admin.site.register(Ingredient, IngredientAdmin, ) 
admin.site.register(Tag, TagAdmin, )
