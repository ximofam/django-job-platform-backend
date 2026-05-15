from rest_framework.permissions import BasePermission


class IsCandidate(BasePermission):
    message = "Bạn phải là ứng viên (Candidate) mới có quyền thực hiện hành động này."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user and request.user.is_candidate


class IsCompanyOwner(BasePermission):
    massage = "Bạn không phải là nhà tuyền dụng hoặc công ty này không thuộc về bạn"

    def has_object_permission(self, request, view, company):
        return request.user and request.user.is_employer and company.employer_profile.user == request.user
