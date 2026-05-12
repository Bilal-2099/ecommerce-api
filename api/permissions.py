from rest_framework import permissions


class IsBusinessUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_business()
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.owner == request.user


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        if hasattr(obj, "user"):
            return obj.user == request.user

        if hasattr(obj, "owner"):
            return obj.owner == request.user

        return False