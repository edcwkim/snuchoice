from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^verify/$', views.confirm_email, name='verify'),
    url(r'^verify/(?P<key>[a-z0-9]+)/$', views.signup, name='verify_signup'),
    url(r'^settings/$', views.Settings.as_view(), name='settings'),
    url(r'^delete_account/$', views.DeleteAccount.as_view(), name='delete_account'),
    url(r'^', include('django.contrib.auth.urls')),
]
