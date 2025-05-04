from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class PMSRecommendationStages(TextChoices):
    # * the values should match the admin panel steps codename value
    INCHARGE = "incharge", _("Incharge")
    DHOS = "dhos", _("DHOS")
    CREDIT_MONITORING = "credit_monitoring", _("Credit Monitoring")
    LOGISTICS_ORDER_MGMT = "logistics", _("Logistic & Order Management")
    CBO = "cbo", _("Chief Business Officer")
    AMD = "amd", _("Additional Managing Director")
    CHAIRMAN = "chairman", _("Honorable Chairman")
    EBS_TEAM = "ebs", _("EBS")
    APPROVED = "approved", _("Approved")
    REJECTED = "rejected", _("Rejected")


EXISTING_PARTY = "existing_party"
