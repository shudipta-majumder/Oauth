from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm
from .models import Role, User


class CustomUserAdmin(UserAdmin):
    admin.site.site_header = "⚙️ One Stop Solution"
    admin.site.site_title = "WDTIL-OSS"
    # Define the fields to be displayed in the user list in the admin panel
    list_display = (
        "username",
        "full_name",
        "email",
        "is_staff",
        "is_superuser",
        "is_management",
        "is_active",
        "recommended",
    )
    # Define the fields to be used in the user creation and editing form in the admin
    # panel
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal Info",
            {
                "fields": (
                    "full_name",
                    "email",
                    "designation",
                    "phone",
                    "supervisor_id",
                    "supervisor_name",
                    "hod_id",
                    "hod_name",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "roles",
                    "is_active",
                    "is_staff",
                    "is_management",
                    "is_superuser",
                    "recommended",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login",)}),
    )
    # Define the fields to be used in the add user form in the admin panel
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "is_management", "password1", "password2"),
            },
        ),
    )
    # Define the search fields to be used in the admin panel's search bar
    search_fields = ("username", "full_name", "email")
    # Define the ordering of the users in the admin panel
    ordering = ("-created_at",)
    form = CustomUserChangeForm


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = [
        "codename",
        "viewname",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "is_active",
    ]
    search_fields = ["codename", "viewname"]
    readonly_fields = ["created_by", "updated_by"]
    ordering = ["-updated_at", "-created_at"]

    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
        if change:
            obj.updated_by = request.user
        else:
            obj.created_by = request.user

        return super().save_model(request, obj, form, change)


# Register the Users model with the custom admin class
admin.site.register(User, CustomUserAdmin)
