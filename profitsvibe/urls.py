from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from accounts.views import home_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home page
    path('', home_view, name='home'),

    # Payment app URLs
    path('', include('payments.urls')),

    # Account app URLs
    path('accounts/', include('accounts.urls')),

    # API URLs
    path('api/', include('api.urls')),

    # Static pages
    path('features/', TemplateView.as_view(template_name='features.html'), name='features'),
    path('pricing/', TemplateView.as_view(template_name='pricing.html'), name='pricing'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
]

# Add media URL patterns for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
