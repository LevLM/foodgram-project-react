from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, data):
        return (request.method in permissions.SAFE_METHODS
                or data.author == request.user)
