from django.contrib import admin


class RoleBasedModelAdmin(admin.ModelAdmin):
    allowed_roles = []  # override ở subclass

    def _has_role_permission(self, request):
        if request.user.is_superuser:
            return True
        return request.user.admin_role in self.allowed_roles

    # --- Override 4 permission methods ---
    def has_view_permission(self, request, obj=None):
        return self._has_role_permission(request)

    def has_add_permission(self, request):
        return self._has_role_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._has_role_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self._has_role_permission(request)

    def has_module_perms(self, request, app_label):
        return self._has_role_permission(request)
