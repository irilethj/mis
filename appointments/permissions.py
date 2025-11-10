from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_admin()
        )


class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_doctor()
        )


class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_patient()
        )


class ConsultationPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_admin():
            return True

        if view.action == "create" and request.user.is_patient():
            return True
        if view.action in ["list", "retrieve"]:
            return True
        if view.action in ["partial_update", "update"]:
            return request.user.is_doctor() or request.user.is_admin()
        if view.action == "destroy":
            return request.user.is_admin() or request.user.is_patient()
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin():
            return True

        if request.user.is_patient():
            try:
                return obj.patient.user_id == request.user.id
            except Exception:
                return False

        if request.user.is_doctor():
            try:
                return obj.doctor.user_id == request.user.id
            except Exception:
                return False

        return False
