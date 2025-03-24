"""Django admin customizations."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from . import models


class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    list_display = ["username", "name", "email"]
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (
            _("permisions"),
            {
                "fields": (
                    "is_staff",
                    "is_active",
                    "is_superuser",
                )
            }
        ),
        (_("Important dates"), {"fields": ("last_login",)})
    )
    readonly_fields = ["last_login"]
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "password1",
                "password2",
                "name",
                "is_active",
                "is_staff",
                "is_superuser",
            )
        }),
    )


admin.site.register(models.User, UserAdmin)
