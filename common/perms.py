from rest_framework.permissions import BasePermission


class IsCandidate(BasePermission):
    message = "Bạn phải là ứng viên mới có quyền thực hiện hành động này."

    def has_permission(self, request, view):
        return request.user and request.user.is_candidate


class IsEmployer(BasePermission):
    message = "Bạn phải là nhà tuyển dụng mới có quyền thực hiện hành động này."

    def has_permission(self, request, view):
        return request.user and request.user.is_employer
