from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from cargar_csv.models import Presupuesto  # Asegúrate de que este es el modelo correcto
from django.http import JsonResponse

def graficos_view(request):
    return render(request, "graficos.html")

def obtener_datos_grafico(request):
    # Datos agrupados por 'tipo'
    datos_tipo = (
        Presupuesto.objects
        .values("tipo")
        .annotate(
            total_compromiso=Sum("compromiso"),
            total_disponible=Sum("disponible")
        )
    )

    categorias = []
    series_compromiso = []
    series_disponible = []

    for dato in datos_tipo:
        categorias.append(dato["tipo"])
        series_compromiso.append(float(dato["total_compromiso"] or 0))
        series_disponible.append(float(dato["total_disponible"] or 0))

    # Datos agrupados por 'secretaria'
    datos_secretaria = (
        Presupuesto.objects
        .values("secretaria")
        .annotate(
            total_compromiso_secretaria=Sum("compromiso"),
            total_disponible_secretaria=Sum("disponible")
        )
    )

    secretarias = []
    series_compromiso_secretaria = []
    series_disponible_secretaria = []

    for dato in datos_secretaria:
        secretarias.append(dato["secretaria"])
        series_compromiso_secretaria.append(float(dato["total_compromiso_secretaria"] or 0))
        series_disponible_secretaria.append(float(dato["total_disponible_secretaria"] or 0))

    # Datos discriminados por tipo de gasto y apilados por secretaría
    datos_tipo_secretaria = (
        Presupuesto.objects
        .values("tipo", "secretaria")
        .annotate(
            total_compromiso=Sum("compromiso"),
            total_disponible=Sum("disponible")
        )
    )

    tipo_secretaria_categorias = list(set([dato["tipo"] for dato in datos_tipo_secretaria]))
    secretarias_tipo_categorias = list(set([dato["secretaria"] for dato in datos_tipo_secretaria]))

    series_tipo_secretaria_compromiso = []
    series_tipo_secretaria_disponible = []

    for secret in secretarias_tipo_categorias:
        compromiso = []
        disponible = []
        for tipo in tipo_secretaria_categorias:
            data = next(
                (item for item in datos_tipo_secretaria if item["secretaria"] == secret and item["tipo"] == tipo),
                {"total_compromiso": 0, "total_disponible": 0}
            )
            compromiso.append(float(data["total_compromiso"] or 0))
            disponible.append(float(data["total_disponible"] or 0))
        series_tipo_secretaria_compromiso.append({"name": secret, "data": compromiso})
        series_tipo_secretaria_disponible.append({"name": secret, "data": disponible})

    # Datos discriminados por secretaría y apilados por tipo de gasto
    datos_secretaria_tipo = (
        Presupuesto.objects
        .values("secretaria", "tipo")
        .annotate(
            total_compromiso=Sum("compromiso"),
            total_disponible=Sum("disponible")
        )
    )

    series_secretaria_tipo_compromiso = []
    series_secretaria_tipo_disponible = []

    for tipo in categorias:
        compromiso = []
        disponible = []
        for secret in secretarias:
            data = next(
                (item for item in datos_secretaria_tipo if item["secretaria"] == secret and item["tipo"] == tipo),
                {"total_compromiso": 0, "total_disponible": 0}
            )
            compromiso.append(float(data["total_compromiso"] or 0))
            disponible.append(float(data["total_disponible"] or 0))
        series_secretaria_tipo_compromiso.append({"name": tipo, "data": compromiso})
        series_secretaria_tipo_disponible.append({"name": tipo, "data": disponible})

    return JsonResponse({
        "categorias": categorias,
        "series": [
            {"name": "Compromiso", "data": series_compromiso},
            {"name": "Disponible", "data": series_disponible},
        ],
        "secretarias": secretarias,
        "seriesSecretaria": [
            {"name": "Compromiso", "data": series_compromiso_secretaria},
            {"name": "Disponible", "data": series_disponible_secretaria},
        ],
        "tipoSecretariaCategorias": tipo_secretaria_categorias,
        "seriesTipoSecretariaCompromiso": series_tipo_secretaria_compromiso,
        "seriesTipoSecretariaDisponible": series_tipo_secretaria_disponible,
        "secretariaTipoCategorias": secretarias_tipo_categorias,
        "seriesSecretariaTipoCompromiso": series_secretaria_tipo_compromiso,
        "seriesSecretariaTipoDisponible": series_secretaria_tipo_disponible,
    })

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("/")
        else:
            return render(request, "login.html", {"error": "Usuario o contraseña incorrectos"})
    return render(request, "login.html")

@login_required
def home_view(request):
    return render(request, "home.html")

def logout_view(request):
    logout(request)
    return redirect("/login/")




@login_required
def vista_secretaria(request):
    # Obtener los datos resumidos de la secretaría
    datos_secretaria = (
        Presupuesto.objects
        .values("secretaria")
        .annotate(
            total_compromiso_secretaria=Sum("compromiso"),
            total_disponible_secretaria=Sum("disponible")
        )
    )

    secretarias = [dato["secretaria"] for dato in datos_secretaria]
    series_compromiso_secretaria = [float(dato["total_compromiso_secretaria"] or 0) for dato in datos_secretaria]
    series_disponible_secretaria = [float(dato["total_disponible_secretaria"] or 0) for dato in datos_secretaria]

    # Obtener los datos detallados por secretaría y agrupar por tipo
    datos_por_secretaria_agrupados = {}
    for secretaria in secretarias:
        detalles = Presupuesto.objects.filter(secretaria=secretaria).values("tipo", "compromiso", "disponible", "credito_actual")
        datos_agrupados = {}
        for detalle in detalles:
            tipo = detalle["tipo"]
            if tipo not in datos_agrupados:
                datos_agrupados[tipo] = {
                    "compromiso": 0.0,
                    "disponible": 0.0,
                    "credito_actual": 0.0,
                }
            datos_agrupados[tipo]["compromiso"] += float(detalle["compromiso"] or 0)
            datos_agrupados[tipo]["disponible"] += float(detalle["disponible"] or 0)
            datos_agrupados[tipo]["credito_actual"] += float(detalle["credito_actual"] or 0)
        datos_por_secretaria_agrupados[secretaria] = datos_agrupados

    # Obtener direcciones únicas por secretaría
    direcciones_por_secretaria = {}
    for secretaria in secretarias:
        direcciones = Presupuesto.objects.filter(secretaria=secretaria).values_list('direccion', flat=True).distinct()
        direcciones_por_secretaria[secretaria] = list(direcciones)

    # Obtener datos detallados por secretaría y dirección
    datos_por_secretaria_direccion = {}
    for secretaria in secretarias:
        direcciones = direcciones_por_secretaria[secretaria]
        datos_direccion = {}
        for direccion in direcciones:
            detalles = Presupuesto.objects.filter(secretaria=secretaria, direccion=direccion).aggregate(
                total_compromiso=Sum('compromiso'),
                total_disponible=Sum('disponible'),
                total_credito_actual=Sum('credito_actual')
            )
            datos_direccion[direccion] = {
                'compromiso': float(detalles['total_compromiso'] or 0),
                'disponible': float(detalles['total_disponible'] or 0),
                'credito_actual': float(detalles['total_credito_actual'] or 0),
            }
        datos_por_secretaria_direccion[secretaria] = datos_direccion

    # Verificar si los datos están correctos
    print("Datos por secretarias agrupados:", datos_por_secretaria_agrupados)
    print("Direcciones por secretaría:", direcciones_por_secretaria)
    print("Datos por secretaría y dirección:", datos_por_secretaria_direccion)

    return render(request, "VistaSecretaria.html", {
        "secretarias": secretarias,
        "series_compromiso_secretaria": series_compromiso_secretaria,
        "series_disponible_secretaria": series_disponible_secretaria,
        "datos_por_secretaria": datos_por_secretaria_agrupados,
        "direcciones_por_secretaria": direcciones_por_secretaria,
        "datos_por_secretaria_direccion": datos_por_secretaria_direccion,
    })