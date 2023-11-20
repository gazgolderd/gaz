from django.contrib import admin
from .models import TelegramUser, Rule, Review, Product, Chapter, Gram


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['username']


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ['bot_rule']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'sold']


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['title']


@admin.register(Gram)
class GramAdmin(admin.ModelAdmin):
    list_display = ['gram']