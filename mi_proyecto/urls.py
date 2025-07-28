from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("autenticacion.urls")),
    path('subir-csv/', include('cargar_csv.urls')),  # Incluye la nueva app
]
