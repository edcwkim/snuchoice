from .core.views import Home
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views import generic

urlpatterns = [
    url(r'^$', Home.as_view(), name="home"),
    url(r'^about/$', generic.TemplateView.as_view(template_name="core/about.html"), name="about"),
    url(r'^policy/$', generic.TemplateView.as_view(template_name="core/policy.html"), name="policy"),
    url(r'^', include('snuchoice.choice.urls')),
    url(r'^', include('snuchoice.auth.urls')),
    url(r'^django-admin/', admin.site.urls),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
