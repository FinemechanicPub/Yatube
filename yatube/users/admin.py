from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from posts.models import User, Follow


class FollowInline(admin.TabularInline):
    model = Follow
    fk_name = 'user'
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = [FollowInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
