from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Group, Post, Comment, Follow

User = get_user_model()


class CommentInline(admin.StackedInline):
    model = Comment
    extra = 0


class FollowInline(admin.TabularInline):
    model = Follow
    fk_name = 'user'
    extra = 0


class PostAdmin(admin.ModelAdmin):
    """Настройки панели администрирования для публикаций."""

    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    list_display_links = ('text',)
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'
    inlines = [CommentInline]


class GroupAdmin(admin.ModelAdmin):
    """Настройки панели администрирования для групп."""

    list_display = ('pk', 'title', 'description')
    list_display_links = ('title',)
    search_fields = ('title', 'description')
    empty_value_display = '-пусто-'
    prepopulated_fields = {"slug": ("title",)}


class UserAdmin(BaseUserAdmin):
    inlines = [FollowInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
