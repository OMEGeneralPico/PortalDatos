from django.urls import path
from .views import login_view, logout_view,vista_movigast, home_view, graficos_view,obtener_datos_grafico,vista_secretaria, vista_pdf_formulario,generar_pdf_presupuesto

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("", home_view, name="home"),
      path("estadisticas/", graficos_view, name="graficos"),
       path("Secretarias/", vista_secretaria, name="secretaria"),
    path("api/grafico/", obtener_datos_grafico, name="api_grafico"),
      path("descargar-informe/", vista_pdf_formulario, name="pdf_formulario"),
    path("descargar-informe/pdf/", generar_pdf_presupuesto, name="generar_pdf"),
   
    path('movigast/', vista_movigast, name='vista_movigast'),
]
