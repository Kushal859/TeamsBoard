from rest_framework.permissions import BasePermission
from .models import Company


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return (
            hasattr(request.user, 'company') and
            request.user.company.role == Company.Role.ADMIN
        )