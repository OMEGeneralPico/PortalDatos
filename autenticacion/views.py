# views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout # Keep if used elsewhere
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from cargar_csv.models import Presupuesto # Ensure this is your correct model
from django.http import JsonResponse
import json # For serializing data if needed, though render handles it for context

# graficos_view and obtener_datos_grafico remain as they are,
# unless you want to apply a similar refactoring strategy to them.
def graficos_view(request):
    return render(request, "graficos.html")

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
@login_required
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


    return render(request, "VistaSecretaria.html", {
        "todos_los_datos_presupuesto_json": json.dumps(datos_filtrados)
    })

    perfil = request.user.userprofile

    if perfil.is_admin:
        queryset = Presupuesto.objects.all()
    else:
        areas = perfil.get_areas_list()
        queryset = Presupuesto.objects.filter(secretaria__in=areas)
    # Fetch all necessary fields from the Presupuesto model
    # 'codigo_sufijo' is NOT fetched here as it's derived later
    todos_los_datos = list(Presupuesto.objects.values(
        "secretaria", "tipo", "direccion", "codigo", # 'codigo' is IntegerField in model
        "credito_actual", "reestructuras", "compromiso", "disponible", # reestructuras is DecimalField
        "año" 
    ))

    for dato in todos_los_datos:
        # Convert monetary fields to float, handling None
        dato["credito_actual"] = float(dato["credito_actual"] or 0)
        dato["reestructuras"] = float(dato["reestructuras"] or 0)
        dato["compromiso"] = float(dato["compromiso"] or 0)
        dato["disponible"] = float(dato["disponible"] or 0)
        
        # Handle 'año', ensuring it's an integer
        dato["año"] = int(dato["año"]) if dato["año"] is not None else 0
        
        # Handle string fields, providing defaults for None
        dato["secretaria"] = dato["secretaria"] if dato["secretaria"] is not None else "Indefinido"
        dato["tipo"] = dato["tipo"] if dato["tipo"] is not None else "Indefinido"
        dato["direccion"] = dato["direccion"] if dato["direccion"] is not None else "Indefinido"
        
        # Process 'codigo' (which is an Integer from DB) to string for manipulation
        # and derive 'codigo_sufijo'
        original_codigo_val = dato.get("codigo") # This is the integer from the database
        processed_codigo_str = str(original_codigo_val) if original_codigo_val is not None else "N/A"
        
        # Store the string version of the code as 'codigo' for the template,
        # if the template expects it as a string.
        # If the template is fine with integer 'codigo' and only uses 'codigo_sufijo' for filtering,
        # you might not need to overwrite dato['codigo'] here.
        # However, previous logic was overwriting it, so we maintain that for consistency.
        dato["codigo"] = processed_codigo_str 

        # Derive 'codigo_sufijo'
        if processed_codigo_str != "N/A":
            parts = processed_codigo_str.split("'")
            if len(parts) == 2 and len(parts[1]) == 2: 
                dato["codigo_sufijo"] = parts[1]
            elif len(processed_codigo_str) >= 2: 
                dato["codigo_sufijo"] = processed_codigo_str[-2:]
            else: 
                dato["codigo_sufijo"] = "XX" # Placeholder for unparseable/short suffixes
        else:
            dato["codigo_sufijo"] = "N/A" # For original None/empty codes
            
    return render(request, "VistaSecretaria.html", {
        "todos_los_datos_presupuesto_json": json.dumps(todos_los_datos)
    })

    todos_los_datos = list(Presupuesto.objects.values(
        "secretaria", "tipo", "direccion", "codigo",
        "credito_actual", "reestructuras", "compromiso", "disponible", # <<< AÑADIDO 'reestructuras'
        "año", "codigo_sufijo" # Assuming codigo_sufijo is still in use from previous changes
    ))

    # print(f"Datos de ejemplo obtenidos de la BD (primeros 1): {todos_los_datos[:1]}")

    for dato in todos_los_datos:
        dato["credito_actual"] = float(dato["credito_actual"] or 0)
        dato["reestructuras"] = float(dato["reestructuras"] or 0) # <<< AÑADIDO PROCESAMIENTO PARA 'reestructuras'
        dato["compromiso"] = float(dato["compromiso"] or 0)
        dato["disponible"] = float(dato["disponible"] or 0) # This will be the value from DB.
                                                                # If it's not correctly updated in DB, use calculated:
                                                                # dato["disponible_calculado"] = dato["credito_actual"] + dato["reestructuras"] - dato["compromiso"]
        dato["año"] = int(dato["año"]) if dato["año"] is not None else 0
        dato["secretaria"] = dato["secretaria"] if dato["secretaria"] is not None else "Indefinido"
        dato["tipo"] = dato["tipo"] if dato["tipo"] is not None else "Indefinido"
        dato["direccion"] = dato["direccion"] if dato["direccion"] is not None else "Indefinido"
        
        original_codigo_val = dato.get("codigo")
        processed_codigo_str = str(original_codigo_val) if original_codigo_val is not None else "N/A"
        dato["codigo"] = processed_codigo_str 

        if "codigo_sufijo" not in dato: # Ensure codigo_sufijo processing if it was there
            if processed_codigo_str != "N/A":
                parts = processed_codigo_str.split("'")
                if len(parts) == 2 and len(parts[1]) == 2: 
                    dato["codigo_sufijo"] = parts[1]
                elif len(processed_codigo_str) >= 2: 
                    dato["codigo_sufijo"] = processed_codigo_str[-2:]
                else: 
                    dato["codigo_sufijo"] = "XX" 
            else:
                dato["codigo_sufijo"] = "N/A"
    
    # print(f"Datos de ejemplo procesados (primeros 1): {todos_los_datos[:1]}")
        
    return render(request, "VistaSecretaria.html", {
        "todos_los_datos_presupuesto_json": json.dumps(todos_los_datos)
    })
    todos_los_datos = list(Presupuesto.objects.values(
        "secretaria", "tipo", "direccion", "codigo",
        "compromiso", "disponible", "credito_actual",
        "año"
    ))

    for dato in todos_los_datos:
        dato["compromiso"] = float(dato["compromiso"] or 0)
        dato["disponible"] = float(dato["disponible"] or 0)
        dato["credito_actual"] = float(dato["credito_actual"] or 0)
        dato["año"] = int(dato["año"]) if dato["año"] is not None else 0
        dato["secretaria"] = dato["secretaria"] if dato["secretaria"] is not None else "Indefinido"
        dato["tipo"] = dato["tipo"] if dato["tipo"] is not None else "Indefinido"
        dato["direccion"] = dato["direccion"] if dato["direccion"] is not None else "Indefinido"
        
        original_codigo_val = dato.get("codigo")
        processed_codigo_str = str(original_codigo_val) if original_codigo_val is not None else "N/A"
        dato["codigo"] = processed_codigo_str # Store the full processed code as string

        if processed_codigo_str != "N/A":
            parts = processed_codigo_str.split("'")
            if len(parts) == 2 and len(parts[1]) == 2: # XX'YY format and YY is 2 chars
                dato["codigo_sufijo"] = parts[1]
            # Fallback for codes like '7412' (no apostrophe) or if YY part from split isn't 2 chars
            elif len(processed_codigo_str) >= 2: 
                dato["codigo_sufijo"] = processed_codigo_str[-2:]
            else: # Code is too short or malformed (e.g. "1", "X'Y")
                dato["codigo_sufijo"] = "XX" # Placeholder for unparseable/short suffixes
        else:
            dato["codigo_sufijo"] = "N/A" # For original None/empty codes

    # print(f"Datos de ejemplo procesados (primeros 3): {todos_los_datos[:3]}")
        
    return render(request, "VistaSecretaria.html", {
        "todos_los_datos_presupuesto_json": json.dumps(todos_los_datos)
    })