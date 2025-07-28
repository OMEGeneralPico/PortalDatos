# A_new_app/urls.py (or wherever your cargar_csv app's urls are defined)
from django.urls import path
from . import views # Assuming views.py is in the same app

urlpatterns = [
    # ... other urls ...
path('upload-presupuesto/', views.upload_presupuesto_bdf, name='url_name_for_upload_presupuesto_bdf'),
path('upload-movigast/', views.upload_movigast_csv, name='upload_movigast_csv'),
  
    
    # URL genérica para subir los CSV de referencia
    # Acepta 'secretaria', 'direccion', o 'actividad' como parámetro
    path('upload-ref/', views.upload_reference_csv, name='upload_reference_csv'),
    
    # URL para subir el CSV principal de MoviGast (apunta a tu vista adaptada)
  

    # Visualización de resumen
  
  
    # ... other urls ...
]