from django.http import HttpResponse
from django.shortcuts import render
import csv
from .models import Presupuesto
import decimal

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

def upload_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        # Verificar si el archivo tiene el formato correcto
        if not csv_file.name.endswith('.csv'):
            return HttpResponse("Por favor sube un archivo CSV válido")
        
        # Leer el archivo CSV
        reader = csv.reader(csv_file.read().decode('utf-8').splitlines())
        
        # Saltar la primera fila de encabezados
        next(reader)
        
        for row in reader:
            if len(row) >= 9:
                try:
                    Presupuesto.objects.create(
                        codigo=row[0],
                        secretaria=row[1],
                        direccion=row[2],
                        tipo=row[3],
                        nombre=row[4] if row[4] else None,
                        credito_actual=clean_and_convert(row[5]),
                        compromiso=clean_and_convert(row[6]),
                        disponible=clean_and_convert(row[7]),
                        año=row[8]
                    )
                except Exception as e:
                    print(f"Error al procesar la fila {row}: {e}")
                    continue

        return HttpResponse("Archivo CSV cargado exitosamente")
    
    return render(request, 'upload_csv.html')
