from logging import getLogger

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from core.constants import CustomPermissions, Groups

logger = getLogger(__name__)


# Base Approval Permission Class
class BaseApprovalPermission(BasePermission):
    """
    Base approval permission class that serves as a template for other approval
    permissions. Subclasses can inherit from this base class to implement specific
    approval logic.

    Attributes:
        message (str): A custom error message to be displayed when permission is denied.
    """

    message = "You don't have the approval permission"

    def _perm_check(self, request: Request, group_name: str, perm_lvl: str) -> bool:
        incharge = request.user.groups.filter(name=group_name).first()

        if not incharge:
            return False

        has_permission = incharge.permissions.filter(codename=perm_lvl).first()

        if not has_permission:
            return False

        return True

    def has_permission(self, request: Request, view) -> bool:
        return super().has_permission(request, view)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        return super().has_object_permission(request, view, obj)


# Member Permission
class MemberPermission(BaseApprovalPermission):
    """
    Permission class for Member. Member users are granted permission
    based on the rules defined in the BaseApprovalPermission class.
    """

    def has_permission(self, request: Request, view) -> bool:
        """
        Check if the user has permission for Member.

        Args:
            request: The HTTP request.
            view: The view being accessed.
            obj: The object being accessed (if applicable).

        Returns:
            bool: True if the user has approval permission, False otherwise.
        """
        return super().has_permission(request, view)


# Incharge Approval Permission
class InchargeApprovalPermission(BaseApprovalPermission):
    """
    Permission class for Incharge approval. Incharge users are granted permission
    based on the rules defined in the BaseApprovalPermission class.
    """

    def has_permission(self, request: Request, view) -> bool:
        """
        Check if the user has permission for Incharge approval.

        Args:
            request: The HTTP request.
            view: The view being accessed.
            obj: The object being accessed (if applicable).

        Returns:
            bool: True if the user has approval permission, False otherwise.
        """
        return self._perm_check(
            request, Groups.INCHARGE, CustomPermissions.INCHARGE_APPROVAL
        )


# HOD Approval Permission
class HODApprovalPermission(BaseApprovalPermission):
    """
    Permission class for Head of Department (HOD) approval. HOD users are granted
    permission based on the rules defined in the BaseApprovalPermission class.
    """

    def has_permission(self, request: Request, view) -> bool:
        """
        Check if the user has permission for HOD approval.

        Args:
            request: The HTTP request.
            view: The view being accessed.
            obj: The object being accessed (if applicable).

        Returns:
            bool: True if the user has approval permission, False otherwise.
        """
        return self._perm_check(request, Groups.HOD, CustomPermissions.HOD_APPROVAL)


# Account Approval Permission
class AccountApprovalPermission(BaseApprovalPermission):
    """
    Permission class for Account approval. Account users are granted permission
    based on the rules defined in the BaseApprovalPermission class.
    """

    def has_permission(self, request: Request, view) -> bool:
        """
        Check if the user has permission for Account approval.

        Args:
            request: The HTTP request.
            view: The view being accessed.
            obj: The object being accessed (if applicable).

        Returns:
            bool: True if the user has approval permission, False otherwise.
        """
        return self._perm_check(
            request, Groups.ACCOUNT, CustomPermissions.ACCOUNT_APPROVAL
        )


# CBO Approval Permission
class CBOApprovalPermission(BaseApprovalPermission):
    """
    Permission class for Chief Business Officer (CBO) approval. CBO users are granted
    permission based on the rules defined in the BaseApprovalPermission class.
    """

    def has_permission(self, request: Request, view) -> bool:
        """
        Check if the user has permission for CBO approval.

        Args:
            request: The HTTP request.
            view: The view being accessed.
            obj: The object being accessed (if applicable).

        Returns:
            bool: True if the user has approval permission, False otherwise.
        """
        return self._perm_check(request, Groups.CBO, CustomPermissions.CBO_APPROVAL)


# AMD Approval Permission
class AMDApprovalPermission(BaseApprovalPermission):
    """
    Permission class for Assistant Managing Director (AMD) approval. AMD users are
    granted permission based on the rules defined in the BaseApprovalPermission class.
    """

    def has_permission(self, request: Request, view) -> bool:
        """
        Check if the user has permission for AMD approval.

        Args:
            request: The HTTP request.
            view: The view being accessed.
            obj: The object being accessed (if applicable).

        Returns:
            bool: True if the user has approval permission, False otherwise.
        """
        return self._perm_check(request, Groups.AMD, CustomPermissions.AMD_APPROVAL)


# Chairman Approval Permission
class ChairmanApprovalPermission(BaseApprovalPermission):
    """
    Permission class for Chairman approval. Chairman users are granted permission
    based on the rules defined in the BaseApprovalPermission class.
    """

    def has_permission(self, request: Request, view) -> bool:
        """
        Check if the user has permission for Chairman approval.

        Args:
            request: The HTTP request.
            view: The view being accessed.
            obj: The object being accessed (if applicable).

        Returns:
            bool: True if the user has approval permission, False otherwise.
        """
        return self._perm_check(
            request, Groups.CHAIRMAN, CustomPermissions.CHAIRMAN_APPROVAL
        )


class IsOwnerOrAdminOrManagementPermission(BasePermission):
    def has_object_permission(self, request: Request, view, obj) -> bool:
        if request.user.is_superuser or request.user.is_management:
            return True
        return obj.created_by == request.user


class IsOwnerAccountOrAdminPermission(BasePermission):
    def has_object_permission(self, request: Request, view, obj) -> bool:
        if request.user.is_superuser:
            return True
        return request.user.username == obj.username


class HasRecommendPermission(BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        return (
            request.user.has_perm("auth_users.can_recommend_salesperson")
            or request.user.is_superuser is True
        )


class UserAccessControl(BasePermission):
    """
    Custom permission to allow specific teams to manage tenders.
    - Tender Team: Can create and update tenders.
    - BI Team: Can update tenders.
    - Management Team: Can only view tenders.
    """

    def has_permission(self, request, view):
        user = request.user

        # Log the request information
        logger.info(
            f"User {user} is trying to access {view} with {request.method} request."
        )

        # Allow GET requests for everyone in the Management, Tender, or BI Team
        if request.method == "GET":
            if user and (
                user.groups.filter(name="Management_Team").exists()
                or user.groups.filter(name="Tender_Team").exists()
                or user.groups.filter(name="BI_Team").exists()
                or user.groups.filter(name="CBO").exists()
                or user.groups.filter(name="AMD").exists()
            ):
                logger.info(f"GET request allowed for user {user} in group.")
                return True
            else:
                logger.warning(f"GET request denied for user {user}.")
                return False

        # Allow POST (create) for Tender Team only
        if request.method == "POST":
            if user and (
                user.groups.filter(name="Tender_Team").exists()
                # or user.groups.filter(name="BI_Team").exists()
            ):
                logger.info(f"POST request allowed for user {user} in Tender Team.")
                return True
            else:
                logger.warning(f"POST request denied for user {user}.")
                return False

        # Allow PUT/PATCH (update) for both Tender Team and BI Team
        if request.method in ["PUT", "PATCH"]:
            if user and (
                user.groups.filter(name="Tender_Team").exists()
                or user.groups.filter(name="BI_Team").exists()
            ):
                logger.info(
                    f"{request.method} request allowed for user {user} in Tender or BI Team."
                )
                return True
            else:
                logger.warning(f"{request.method} request denied for user {user}.")
                return False

        # Deny other methods like DELETE
        logger.error(f"{request.method} request is not allowed for user {user}.")
        return False


class UserAccessControlForAnalysisTeam(UserAccessControl):
    """
    Custom permission to allow only BI Team to manage ProductAnalysis and ProductSpacification.
    - BI Team: Can create ProductAnalysis and delete ProductAnalysis or ProductSpacification.
    """

    def has_permission(self, request, view):
        user = request.user
        view_name = view.__class__.__name__

        # Log the request information
        logger.info(
            f"User {user} is trying to access {view_name} with {request.method} request."
        )

        # Allow POST requests only for BI Team for ProductAnalysisCreateView
        if request.method == "POST" and view_name == "ProductAnalysisCreateView":
            if user and user.groups.filter(name="BI_Team").exists():
                logger.info(f"POST request allowed for {view_name} by user {user}.")
                return True
            else:
                logger.warning(f"POST request denied for {view_name} by user {user}.")
                return False

        # Allow DELETE requests only for BI Team for ProductAnalysisDeleteView and ProductSpacificationDeleteView
        if request.method == "DELETE" and view_name in [
            "ProductAnalysisDeleteView",
            "ProductSpacificationDeleteView",
        ]:
            if user and user.groups.filter(name="BI_Team").exists():
                logger.info(f"DELETE request allowed for {view_name} by user {user}.")
                return True
            else:
                logger.warning(f"DELETE request denied for {view_name} by user {user}.")
                return False

        # Deny all other requests
        logger.warning(
            f"{request.method} request is not allowed for {view_name} by user {user}."
        )
        return False
