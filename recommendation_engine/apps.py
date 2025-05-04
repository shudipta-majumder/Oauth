from django.apps import AppConfig


class RecommendationSystemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "recommendation_engine"
    verbose_name = "Approval Engine"

    def ready(self):
        from . import signals  # noqa F401
