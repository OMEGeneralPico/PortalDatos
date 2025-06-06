# cargar_csv/views.py

from django.http import HttpResponse
from django.shortcuts import render
import csv
from .models import Presupuesto, TipoGasto # Asegúrate que models.py esté en la misma app
import decimal

# Helper function mejorada para limpiar y convertir valores monetarios de CSV
def clean_and_convert(value):
    # Verificar si el valor es un '-' y convertirlo a '0'
    if value.strip() == '-':
        return decimal.Decimal(0)
    
    # Eliminar el símbolo del dólar y las comas
    value = value.replace('$', '').replace(',', '').strip()
    
    # Intentar convertir el valor a decimal
    try:
        return decimal.Decimal(value)
    except decimal.InvalidOperation:
        # Si no se puede convertir, devuelve 0
        return decimal.Decimal(0)

def clean_and_convert(value):
    # Verificar si el valor es un '-' y convertirlo a '0'
    if value.strip() == '-':
        return decimal.Decimal(0)
    
    # Eliminar el símbolo del dólar y las comas
    value = value.replace('$', '').replace(',', '').strip()
    
    # Intentar convertir el valor a decimal
    try:
        return decimal.Decimal(value)
    except decimal.InvalidOperation:
        # Si no se puede convertir, devuelve 0
        return decimal.Decimal(0)

# Vista para cargar datos de Presupuesto
def upload_presupuesto_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file_presupuesto'):
        csv_file = request.FILES['csv_file_presupuesto']
        
        if not csv_file.name.endswith('.csv'):
            return HttpResponse("Por favor sube un archivo CSV válido para Presupuesto.")
        
        processed_count = 0
        created_count = 0
        updated_count = 0
        error_rows = []

        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)
            
            headers = next(reader) # Saltar fila de encabezados
            print(f"Encabezados CSV Presupuesto: {headers}")

            # Estructura CSV esperada (10 columnas):
            # codigo, secretaria, direccion, tipo, nombre, credito_actual, reestructuras, compromiso, disponible, año
            #   0       1           2         3     4           5               6             7            8        9

            for row_number, row in enumerate(reader, 1):
                if len(row) >= 10: 
                    try:
                        codigo_csv = int(str(row[0]).strip()) # Convertir a string primero por si tiene espacios
                        año_csv = int(str(row[9]).strip())

                        defaults_data = {
                            'secretaria': str(row[1]).strip(),
                            'direccion': str(row[2]).strip(),
                            'tipo': str(row[3]).strip(),
                            'nombre': str(row[4]).strip() if str(row[4]).strip() else None,
                           'credito_actual': clean_and_convert(row[5]),
'reestructuras': clean_and_convert(row[6]),
'compromiso': clean_and_convert(row[7]),
'disponible': clean_and_convert(row[8]),

                            # 'codigo' y 'año' se usan para buscar, no van en defaults_data
                        }

                        obj, created = Presupuesto.objects.update_or_create(
                            codigo=codigo_csv,
                            año=año_csv,
                            defaults=defaults_data
                        )
                        
                        processed_count += 1
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

                    except ValueError as ve:
                        print(f"Error de valor en fila {row_number} {row}: {ve}. Verifique que código y año sean números válidos.")
                        error_rows.append({'row': row_number, 'data': row, 'error': str(ve)})
                        continue
                    except Exception as e:
                        print(f"Error al procesar la fila {row_number} {row}: {e}")
                        error_rows.append({'row': row_number, 'data': row, 'error': str(e)})
                        continue
                else:
                    print(f"Fila {row_number} ignorada: número de columnas insuficiente ({len(row)}). Se esperaban 10.")
                    error_rows.append({'row': row_number, 'data': row, 'error': 'Columnas insuficientes'})
            
            summary_message = (
                f"Archivo CSV de Presupuesto procesado: <br>"
                f"Total de filas procesadas (o intentadas): {processed_count}.<br>"
                f"Registros creados: {created_count}.<br>"
                f"Registros actualizados: {updated_count}.<br>"
                f"Filas con errores: {len(error_rows)}."
            )
            if error_rows:
                summary_message += "<br><br>Errores detallados:<br>"
                for err in error_rows[:10]: # Mostrar hasta 10 errores
                    summary_message += f"Fila {err['row']}: {err['error']} (Datos: {', '.join(err['data'])})<br>"
            return HttpResponse(summary_message)

        except UnicodeDecodeError:
            return HttpResponse("Error de decodificación: Asegúrese de que el archivo CSV esté en formato UTF-8.")
        except Exception as e:
            return HttpResponse(f"Error al leer el archivo CSV: {e}")
            
    return render(request, 'upload_csv.html') 

# Vista para cargar datos de TipoGasto
def upload_tipo_gasto_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file_tipo_gasto'):
        csv_file = request.FILES['csv_file_tipo_gasto']
        
        if not csv_file.name.endswith('.csv'):
            return HttpResponse("Por favor sube un archivo CSV válido para Tipo de Gasto.")
        
        processed_count = 0
        created_count = 0
        updated_count = 0
        error_rows = []

        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)
            
            headers = next(reader)
            print(f"Encabezados CSV TipoGasto: {headers}") 
            
            for row_number, row in enumerate(reader, 1):
                if len(row) >= 3:
                    try:
                        # Asumiendo que 'tipo' y 'categoria' juntos hacen una clave única, o solo 'tipo' si es único.
                        # Si 'tipo' por sí solo debe ser único para identificar, usa solo ese para el lookup.
                        # Si la combinación (tipo, categoria) es la que identifica una entrada única, usa ambos.
                        # Aquí asumiré que 'tipo' es el identificador principal para actualizar o crear.
                        tipo_csv = int(str(row[0]).strip())
                        
                        defaults_data = {
                            'categoria': int(str(row[1]).strip()),
                            'descripcion': str(row[2]).strip()
                        }

                        tipo_gasto, created = TipoGasto.objects.update_or_create(
                            tipo=tipo_csv, # Clave para buscar
                            defaults=defaults_data
                        )
                        
                        processed_count +=1
                        if created:
                            created_count +=1
                        else:
                            updated_count +=1
                            
                    except ValueError as ve:
                        print(f"Error de valor en fila {row_number} {row} para TipoGasto: {ve}.")
                        error_rows.append({'row': row_number, 'data': row, 'error': str(ve)})
                        continue
                    except Exception as e:
                        print(f"Error al procesar la fila {row_number} {row} para TipoGasto: {e}")
                        error_rows.append({'row': row_number, 'data': row, 'error': str(e)})
                        continue
                else:
                    print(f"Fila {row_number} ignorada para TipoGasto (menos de 3 columnas): {row}")
                    error_rows.append({'row': row_number, 'data': row, 'error': 'Columnas insuficientes'})

            summary_message = (
                f"Archivo CSV de Tipo de Gasto procesado: <br>"
                f"Total de filas procesadas (o intentadas): {processed_count}.<br>"
                f"Registros creados: {created_count}.<br>"
                f"Registros actualizados: {updated_count}.<br>"
                f"Filas con errores: {len(error_rows)}."
            )
            if error_rows:
                summary_message += "<br><br>Errores detallados:<br>"
                for err in error_rows[:10]: # Mostrar hasta 10 errores
                    summary_message += f"Fila {err['row']}: {err['error']} (Datos: {', '.join(err['data'])})<br>"
            return HttpResponse(summary_message)
        except UnicodeDecodeError:
            return HttpResponse("Error de decodificación: Asegúrese de que el archivo CSV (Tipo Gasto) esté en formato UTF-8.")
        except Exception as e:
            return HttpResponse(f"Error al leer el archivo CSV de Tipo de Gasto: {e}")
    
    return render(request, 'upload_csv.html') # O la plantilla específica para subir TipoGasto