from rest_framework.permissions import BasePermission


class IsCompanyOwner(BasePermission):
    massage = "Bạn không phải là nhà tuyền dụng hoặc công ty này không thuộc về bạn"

    def has_object_permission(self, request, view, company):
        return request.user and request.user.is_employer and company.employer_profile.user == request.user
