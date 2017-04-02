from django.conf.urls import url
from django.contrib import admin

from mixpanel_django_graphos.views import ReportActivityView


admin.site.index_template = 'admin/index.html'
admin.autodiscover()


def get_admin_urls(urls):
    """
    Extend admin to include additional urls
    """
    def get_urls():
        my_urls = [url(r'^activity-report/$', admin.site.admin_view(
            ReportActivityView.as_view()), name='activity-report')]
        return my_urls + urls
    return get_urls

admin_urls = get_admin_urls(admin.site.get_urls())
admin.site.get_urls = admin_urls

urlpatterns = [
    url(r'^admin/', admin.site.urls),
]
