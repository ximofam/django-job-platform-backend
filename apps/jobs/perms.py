from rest_framework.permissions import BasePermission


class IsJobOwner(BasePermission):
    message = 'Bạn không có quyền thực hiện hành động này với job này.'

    def has_object_permission(self, request, view, obj):
        try:
            return obj.company == request.user.employer_profile.company
        except AttributeError:
            return False


class CanPostJob(BasePermission):
    message = "Bạn không phải employer hoặc account employer của bạn chưa được duyệt"

    def has_permission(self, request, view):
        user = request.user

        return user and user.is_employer and user.has_perm("jobs.add_job")


class IsEmployerOrCandidate(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_employer or user.is_candidate
