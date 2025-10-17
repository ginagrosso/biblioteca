"""
URL configuration for proyecto_biblioteca project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # URLs de autenticación
    path('', include('gestion_libros.urls')),  # Incluir las URLs de gestion_libros
]