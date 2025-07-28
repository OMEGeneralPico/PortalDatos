# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from cargar_csv.models import Presupuesto, Actividad, Secretaria,Direccion
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import json
from cargar_csv.models import MoviGast
from datetime import datetime
from io import BytesIO
from collections import defaultdict




# graficos_view and obtener_datos_grafico remain as they are,
# unless you want to apply a similar refactoring strategy to them.
def graficos_view(request):
    return render(request, "graficos.html")
def vista_pdf_formulario(request):
    secretarias = Presupuesto.objects.values_list("secretaria", flat=True).distinct()
    direcciones = Presupuesto.objects.values_list("direccion", flat=True).distinct()
    tipos = Presupuesto.objects.values_list("tipo", flat=True).distinct()

    return render(request, "formulario_pdf.html", {
        "secretarias": secretarias,
        "direcciones": direcciones,
        "tipos": tipos,
    })

def generar_pdf_presupuesto(request):
    secretaria = request.GET.get("secretaria")
    direcciones = request.GET.getlist("direccion")
    tipos = request.GET.getlist("tipo")

    datos = Presupuesto.objects.filter(secretaria=secretaria)

    if direcciones:
        datos = datos.filter(direccion__in=direcciones)

    if tipos:
        datos = datos.filter(tipo__in=tipos)

    for d in datos:
        d.credito_modificado = d.credito_actual + d.reestructuras

    context = {
        "secretaria": secretaria,
        "direccion": ", ".join(direcciones) if direcciones else "Todas",
        "tipo": ", ".join(tipos) if tipos else "Todos",
        "datos": datos,
        "año": 2025,
        "grafico_base64": "",
        "grafico_barras_base64": "",
    }

    html_string = render_to_string("pdf_reporte_presupuesto.html", context)

    result = BytesIO()
    pdf = pisa.CreatePDF(src=html_string, dest=result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="informe_presupuesto.pdf"'
        return response
    else:
        return HttpResponse("Error al generar el PDF", status=400)
def obtener_datos_grafico(request):
    # This function can also be refactored to send more raw data if
    # graficos.html is equipped to process it similarly.
    # For now, keeping it as is, as the main request pertains to VistaSecretaria.html

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

    secretarias_list = [] # Renamed to avoid conflict
    series_compromiso_secretaria_list = [] # Renamed
    series_disponible_secretaria_list = [] # Renamed

    for dato in datos_secretaria:
        secretarias_list.append(dato["secretaria"])
        series_compromiso_secretaria_list.append(float(dato["total_compromiso_secretaria"] or 0))
        series_disponible_secretaria_list.append(float(dato["total_disponible_secretaria"] or 0))

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
        for tipo_cat in tipo_secretaria_categorias: # Renamed to avoid conflict
            data = next(
                (item for item in datos_tipo_secretaria if item["secretaria"] == secret and item["tipo"] == tipo_cat),
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

    for tipo_val in categorias: # Use previously generated 'categorias'
        compromiso = []
        disponible = []
        for secret_val in secretarias_list: # Use previously generated 'secretarias_list'
            data = next(
                (item for item in datos_secretaria_tipo if item["secretaria"] == secret_val and item["tipo"] == tipo_val),
                {"total_compromiso": 0, "total_disponible": 0}
            )
            compromiso.append(float(data["total_compromiso"] or 0))
            disponible.append(float(data["total_disponible"] or 0))
        series_secretaria_tipo_compromiso.append({"name": tipo_val, "data": compromiso})
        series_secretaria_tipo_disponible.append({"name": tipo_val, "data": disponible})

    return JsonResponse({
        "categorias": categorias,
        "series": [
            {"name": "Compromiso", "data": series_compromiso},
            {"name": "Disponible", "data": series_disponible},
        ],
        "secretarias": secretarias_list,
        "seriesSecretaria": [
            {"name": "Compromiso", "data": series_compromiso_secretaria_list},
            {"name": "Disponible", "data": series_disponible_secretaria_list},
        ],
        "tipoSecretariaCategorias": tipo_secretaria_categorias,
        "seriesTipoSecretariaCompromiso": series_tipo_secretaria_compromiso,
        "seriesTipoSecretariaDisponible": series_tipo_secretaria_disponible,
        "secretariaTipoCategorias": secretarias_tipo_categorias, # This was secretarias_tipo_categorias, check if intended
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
def vista_movigast(request):
    # --- Filtro inicial por perfil de usuario
    perfil = request.user.userprofile
    if perfil.is_admin:
        queryset = MoviGast.objects.all()
    else:
        areas_permitidas = perfil.get_areas_list()
        queryset = MoviGast.objects.filter(direccion__in=areas_permitidas)

    # --- Obtención de filtros del frontend
    direccion_filter = request.GET.get('direccion')
    gasto_filter = request.GET.get('gasto')
    actividad_filter = request.GET.get('actividad')

    # --- Aplicación de filtros adicionales del frontend
    if direccion_filter:
        queryset = queryset.filter(direccion=direccion_filter)
    if gasto_filter:
        queryset = queryset.filter(gasto=gasto_filter)
    if actividad_filter:
        queryset = queryset.filter(actividad=actividad_filter)

    # --- Diccionarios de mapeo para códigos y descripciones
    direcciones_dict = dict(Direccion.objects.values_list('code', 'desc'))
    actividades_dict = dict(Actividad.objects.values_list('code', 'desc'))

    # --- Listados para los dropdown de filtros
    direcciones_listado = sorted([(code, desc) for code, desc in direcciones_dict.items()])
    actividades_listado = sorted([(code, desc) for code, desc in actividades_dict.items()])
    gastos_listado = sorted(list(MoviGast.objects.values_list('gasto', flat=True).distinct()))

    # --- Datos para el gráfico principal (ApexCharts)
    data_por_mes = queryset.values('mes').annotate(total_importe=Sum('importe')).order_by('mes')
    MESES_ES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    chart_labels = [MESES_ES.get(d['mes']) for d in data_por_mes]
    meses_data = [float(d['total_importe']) for d in data_por_mes]
    meses_para_acordeon = {d['mes']: MESES_ES.get(d['mes']) for d in data_por_mes}

    # --- Función auxiliar para la pestaña "Detalle por Mes"
    def procesar_datos_acordeon(qs, group_field, desc_dict=None):
        datos_agrupados = defaultdict(lambda: {'items': [], 'total': 0})
        datos_qs = qs.values('mes', group_field).annotate(total=Sum('importe')).order_by('mes', group_field)
        
        for d in datos_qs:
            mes = d['mes']
            codigo = d[group_field]
            nombre = desc_dict.get(codigo, f"Código {codigo}") if desc_dict else codigo
            
            item_data = {'codigo': codigo, 'nombre': nombre, 'total': float(d['total'])}
            datos_agrupados[mes]['items'].append(item_data)
            datos_agrupados[mes]['total'] += float(d['total'])
        
        for mes in datos_agrupados:
            datos_agrupados[mes]['items'].sort(key=lambda x: x['nombre'])
        return dict(datos_agrupados)

    # --- Función auxiliar para la pestaña "Consolidado por Filtro" (CON LA MODIFICACIÓN)
    def procesar_datos_por_filtro(qs, group_field, desc_dict=None):
        datos_filtrados = defaultdict(lambda: {'items': [], 'total': 0})
        datos_qs = qs.values('mes', group_field).annotate(total_importe=Sum('importe')).order_by(group_field, 'mes')
        
        for d in datos_qs:
            codigo = d[group_field]
            nombre_grupo = f"{codigo} - {desc_dict.get(codigo, 'N/A')}" if desc_dict else codigo
            
            item_data = {
                'mes_numero': d['mes'],  # <-- Campo añadido para ordenar
                'mes_nombre': MESES_ES.get(d['mes']),
                'total_importe': float(d['total_importe'])
            }
            datos_filtrados[nombre_grupo]['items'].append(item_data)
            datos_filtrados[nombre_grupo]['total'] += float(d['total_importe'])
        return dict(sorted(datos_filtrados.items()))

    # --- Procesamiento de datos para las pestañas
    context = {
        'direcciones_listado': direcciones_listado,
        'gastos_listado': gastos_listado,
        'actividades_listado': actividades_listado,
        'direccion_filter': direccion_filter,
        'gasto_filter': gasto_filter,
        'actividad_filter': actividad_filter,
        
        'chart_labels': chart_labels,
        'meses_data': meses_data,
        'meses_para_acordeon': meses_para_acordeon,
        
        'meses_transpuestos_direccion': procesar_datos_acordeon(queryset, 'direccion', direcciones_dict),
        'meses_transpuestos_gasto': procesar_datos_acordeon(queryset, 'gasto'),
        'meses_transpuestos_actividad': procesar_datos_acordeon(queryset, 'actividad', actividades_dict),
        
        'filtro_direccion': procesar_datos_por_filtro(queryset, 'direccion', direcciones_dict),
        'filtro_gasto': procesar_datos_por_filtro(queryset, 'gasto'),
        'filtro_actividad': procesar_datos_por_filtro(queryset, 'actividad', actividades_dict),
    }

    return render(request, 'ListadoMensualGasto.html', context)

def vista_secretaria(request):
    perfil = request.user.userprofile
    areas_permitidas = perfil.get_areas_list() if not perfil.is_admin else []

    queryset = Presupuesto.objects.all()  # Siempre traemos todo, luego filtramos por sufijo

    todos_los_datos = list(queryset.values(
        "secretaria", "tipo", "direccion", "codigo",
        "credito_actual", "reestructuras", "compromiso", "disponible",
        "año"
    ))

    datos_filtrados = []

    for dato in todos_los_datos:
        dato["credito_actual"] = float(dato["credito_actual"] or 0)
        dato["reestructuras"] = float(dato["reestructuras"] or 0)
        dato["compromiso"] = float(dato["compromiso"] or 0)
        dato["disponible"] = float(dato["disponible"] or 0)
        dato["año"] = int(dato["año"]) if dato["año"] is not None else 0
        dato["secretaria"] = dato["secretaria"] if dato["secretaria"] is not None else "Indefinido"
        dato["tipo"] = dato["tipo"] if dato["tipo"] is not None else "Indefinido"
        dato["direccion"] = dato["direccion"] if dato["direccion"] is not None else "Indefinido"

        original_codigo_val = dato.get("codigo")
        processed_codigo_str = str(original_codigo_val) if original_codigo_val is not None else "N/A"
        dato["codigo"] = processed_codigo_str

        if processed_codigo_str != "N/A":
            parts = processed_codigo_str.split("'")
            codigo_str = str(dato.get("codigo") or "")  # Siempre string, por seguridad

        # Prefijo (primeros dos caracteres si existen)
        if len(codigo_str) >= 2:
            dato["codigo_prefijo"] = codigo_str[:2]
        else:
            dato["codigo_prefijo"] = "00"  # o "N/A" si preferís

        # Sufijo (últimos dos caracteres si existen)
        if len(codigo_str) >= 2:
            dato["codigo_sufijo"] = codigo_str[-2:]
        else:
            dato["codigo_sufijo"] = "XX"  # o "N/A" también


        # ✅ FILTRAMOS por codigo_sufijo si NO es admin
        if perfil.is_admin or dato["codigo_prefijo"] in areas_permitidas:
         datos_filtrados.append(dato)

    # Ya tenés datos_filtrados
    prefijos_usuario = set(d["codigo_prefijo"] for d in datos_filtrados)

    mostrar_direcciones = len(prefijos_usuario) > 1

    return render(request, "VistaSecretaria.html", {
    "todos_los_datos_presupuesto_json": json.dumps(datos_filtrados),
    "mostrar_direcciones": mostrar_direcciones
})