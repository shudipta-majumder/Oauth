from typing import Any

from django.contrib import admin
from django.db import models
from django.forms import CheckboxSelectMultiple
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from .models import Menu


class MainMenuFilter(admin.SimpleListFilter):
    title = _("Main Menu")
    parameter_name = "codename"

    def lookups(self, request, model_admin):
        without_parents = (
            model_admin.get_queryset(request)
            .filter(parent_menu__isnull=True, path__isnull=True)
            .order_by("parent_menu__codename")
            .values_list("codename", "viewname")
        )
        return without_parents

    def queryset(self, request: HttpRequest, queryset):
        if self.value():
            group = request.GET.get("codename")
            return queryset.filter(parent_menu__codename=group)


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = (
        "codename",
        "viewname",
        "path",
        "order",
        "parent_menu",
        "is_active",
    )
    search_fields = ("codename", "viewname", "path")
    list_filter = ("is_active", "roles", MainMenuFilter)
    list_editable = ("order", "path", "viewname", "is_active")

    readonly_fields = ("created_at", "created_by", "updated_at", "updated_by")
    formfield_overrides = {
        models.ManyToManyField: {
            "widget": CheckboxSelectMultiple,
        }
    }

    def save_model(self, request: Any, obj: Menu, form: Any, change: Any) -> None:
        if not change:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        return super().save_model(request, obj, form, change)
