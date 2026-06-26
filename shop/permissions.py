from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает GET, HEAD, OPTIONS всем,
    а POST, PUT, PATCH, DELETE только для пользователей с ролью 'admin'.
    """
    def has_permission(self, request, view):
        # Безопасные методы (GET, HEAD, OPTIONS) разрешены всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Для остальных методов проверяем, что пользователь аутентифицирован и имеет роль admin
        if not request.user.is_authenticated:
            return False
        # Проверяем, есть ли у пользователя профиль и роль = 'admin'
        return hasattr(request.user, 'profile') and request.user.profile.role == 'admin'
    
class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешает доступ к объекту только его владельцу или администратору.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
            return True
        return hasattr(obj, 'user') and obj.user == request.user