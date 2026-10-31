from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
        'created_at',
    )

    search_fields = ('username', 'email')

    list_filter = (
        'is_staff',
        'is_active',
        'is_superuser',
    )

    readonly_fields = ('created_at', 'updated_at')