from django.contrib import admin

from .models import Group, Post, Comment, Follow


class CommentInline(admin.StackedInline):
    model = Comment
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


class CommentAdmin(admin.ModelAdmin):
    """Настройки панели администрирования для комментариев"""

    list_display = ('text', 'author', 'post')
    list_editable = ('author',)
    search_fields = ('text', 'author__username')


class FollowAdmin(admin.ModelAdmin):
    """Настройки панели администрирования для подписок"""

    list_display = ('__str__', 'user', 'author')
    list_editable = ('user', 'author')
    search_fields = ('user__username', 'author__username')


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Comment, CommentAdmin)
