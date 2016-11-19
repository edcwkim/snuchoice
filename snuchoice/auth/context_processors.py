from django.contrib.auth.views import redirect_to_login

def login_redirect(request):
    redirect = redirect_to_login(request.get_full_path(), "verify")
    if not request.user.is_authenticated:
        return {
            'login_url': redirect.url,
            'query_string': request.META['QUERY_STRING'],
        }
    else:
        return {}
