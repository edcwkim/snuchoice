from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import resolve_url


class AjaxOnlyMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404('AJAX only')
        return super().dispatch(request, *args, **kwargs)


class VerifyRequiredMixin(LoginRequiredMixin):
    def get_login_url(self):
        return resolve_url("verify")
