# A_new_app/urls.py (or wherever your cargar_csv app's urls are defined)
from django.urls import path
from . import views # Assuming views.py is in the same app

urlpatterns = [
    # ... other urls ...
    path('upload-presupuesto/', views.upload_presupuesto_csv, name='url_name_for_upload_presupuesto_csv'),
    path('upload-tipo-gasto/', views.upload_tipo_gasto_csv, name='url_name_for_upload_tipo_gasto_csv'),
    # ... other urls ...
]