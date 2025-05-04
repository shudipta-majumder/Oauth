from django.urls import path

from .views import ApprovalStepViewSet, RecommendationDecisionView

urlpatterns = [
    path(
        "approval-paths/<str:process>",
        ApprovalStepViewSet.as_view(),
    ),
    path(
        "approvals/<int:pk>",
        RecommendationDecisionView.as_view(),
    ),
]
