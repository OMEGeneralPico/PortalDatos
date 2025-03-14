from django.urls import path
from .views import login_view, logout_view, home_view, graficos_view,obtener_datos_grafico,vista_secretaria

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("", home_view, name="home"),
      path("estadisticas/", graficos_view, name="graficos"),
       path("Secretarias/", vista_secretaria, name="secretaria"),
    path("api/grafico/", obtener_datos_grafico, name="api_grafico"),
]
