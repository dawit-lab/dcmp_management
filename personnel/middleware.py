from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """
    Redirect users flagged with must_change_password=True to the change-password
    page until they change it. Skips admin, login, logout, static, and the
    change-password URL itself.
    """
    EXEMPT_URL_NAMES = {
        'login', 'logout', 'change-password', 'password_reset',
        'password_reset_done', 'password_reset_confirm',
        'password_reset_complete',
    }
    EXEMPT_PREFIXES = (
        '/admin/', '/static/', '/media/', '/__debug__/', '/api/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Superusers are never forced
            if not request.user.is_superuser:
                profile = getattr(request.user, 'profile', None)
                if profile and profile.must_change_password:
                    path = request.path_info
                    url_name = getattr(request.resolver_match, 'url_name', None)

                    if url_name not in self.EXEMPT_URL_NAMES and \
                       not path.startswith(self.EXEMPT_PREFIXES):
                        return redirect('change-password')

        return self.get_response(request)