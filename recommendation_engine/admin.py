from django.contrib import admin

from .models import (
    ApprovalQueue,
    ApprovalStep,
    ApprovalUser,
    RecommendationProcess,
    RecommendationSystem,
)


class RecommendationProcessInline(admin.TabularInline):
    model = RecommendationProcess
    extra = 0
    exclude = (
        "created_by",
        "updated_by",
    )


@admin.register(ApprovalQueue)
class ApprovalQueueAdmin(admin.ModelAdmin):
    list_display = ("object_id", "node", "content_type", "status")
    search_fields = ("object_id",)
    list_filter = (
        "content_type",
        "status",
    )
    readonly_fields = (
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )


@admin.register(RecommendationSystem)
class RecommendationSystemAdmin(admin.ModelAdmin):
    list_display = ("codename", "viewname")
    inlines = (RecommendationProcessInline,)
    exclude = (
        "created_by",
        "updated_by",
    )


@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "system",
        "process",
        "codename",
        "forward_step",
        "backward_step",
    )
    exclude = (
        "created_by",
        "updated_by",
    )
    list_filter = ("system__viewname", "process__viewname")
    list_select_related = True


@admin.register(ApprovalUser)
class ApprovalUserAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "approval_step",
        "forward_step",
        "backward_step",
        "is_active",
    )
    exclude = (
        "created_by",
        "updated_by",
    )
    list_display_links = ("user",)
    list_filter = (
        "approval_step__system__viewname",
        "approval_step__process__viewname",
        "user",
    )
    ordering = ("approval_step__forward_step",)

    @admin.display(empty_value="???")
    def forward_step(self, obj: ApprovalUser) -> int:
        return obj.approval_step.forward_step

    @admin.display(empty_value="???")
    def backward_step(self, obj: ApprovalUser) -> int:
        return obj.approval_step.backward_step
