from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q

class EmailBackend(ModelBackend):
    """
    Custom authentication backend yang memungkinkan login dengan email atau username
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Coba cari user berdasarkan email atau username
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
