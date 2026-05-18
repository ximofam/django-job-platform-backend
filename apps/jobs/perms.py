from rest_framework.permissions import BasePermission


class IsJobOwner(BasePermission):
    message = 'Bạn không có quyền thực hiện hành động này với job này.'

    def has_object_permission(self, request, view, obj):
        try:
            return obj.company == request.user.employer_profile.company
        except AttributeError:
            return False
