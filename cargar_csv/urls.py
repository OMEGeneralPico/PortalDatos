from django.urls import path
from . import views

urlpatterns = [
    path('subir-csv/', views.upload_csv, name='uploads_csv'),
]
