from dbfread import DBF
from django.core.files.storage import FileSystemStorage
import os
from django.http import HttpResponse
from django.shortcuts import render
import decimal
from datetime import datetime
from .models import Presupuesto, TipoGasto, MoviGast, Secretaria, Direccion, Actividad
import pandas as pd
from decimal import Decimal
SECRETARIA_MAP = {
    '1': 'Cons. Delibera',
    '2': 'Intendencia',
    '3': 'Gobierno Sec.',
    '4': 'Gestion Urbana',
    '5': 'Ambiente y serv',
    '6': 'Des Social',
    '8': 'Exteriores',
    '7': 'Economia',
    '9': 'Otros',
}

DIRECCION_MAP = {
    '10': 'Cons. Delibera', 
    '20': 'Intendencia', 
    '21': 'Faltas', 
    '22': 'Asuntos Legales', 
    '23': 'Comunicacion',
    '24': 'Modern. Tecn', 
    '25': 'Protocolo', 
    '26': 'Gest. Adm. Art', 
    '30': 'Gobierno Sec.', 
    '31': 'Recursos Hum',
    '32': 'Prevenc. Ciud.', 
    '33': 'Educ. y Cultura', 
    '34': 'Rel.Institucional', 
    '35': 'Juventud', 
    '36': 'Choferes',
    '37': 'Educacion', 
    '38': 'Deportes', 
    '40': 'Gestion Urbana', 
    '41': 'Serv. Cons', 
    '42': 'Obras Munici',
    '43': 'Obras Particul', 
    '44': 'Plan. Catastro', 
    '45': 'Dis. y Planifica',
    '50': 'Ambiente y serv',
    '51': 'Des. Sustentab.', 
    '52': 'Serv. Publicos', 
    '53': 'Arbolado', 
    '54': 'Gestion Amb', 
    '55': 'Zoonosis y vec',
    '56': 'RRU', 
    '57': 'Girsu', 
    '60': 'Des Social',
    '61': 'Familia', 
    '62': 'Des. Infantil', 
    '63': 'Des Territorial',
    '64': 'Unid. Niñez', 
    '65': 'Polit. Genero', 
    '70': 'Economia', 
    '71': 'Contaduria', 
    '72': 'Rentas',
    '73': 'Dir. Comercio', 
    '74': 'Des. Econo', 
    '75': 'Tesoreria', 
    '80': 'Asfalto', 
    '81': 'Caminos Vec',
    '97': 'No Programatica', 
    '98': 'Prov y Nacion', 
    '99': 'No Programatica',
}

TIPO_MAP = {
    '1': 'Personal',
    '2': 'Bienes de Consumo',
    '3': 'No Personales',
    '4': 'Transf. Sociales',
    '5': 'Bienes de Capital',
    '6': 'Trabajo Publico',
    '7': 'Prestamos',
    '8': 'Serv. Especiales',
    '10': 'Deuda Publica',
}
def clean_and_convert(value):
    try:
        return decimal.Decimal(str(value).replace('$', '').replace(',', '').strip())
    except:
        return decimal.Decimal(0)

def upload_presupuesto_bdf(request):
    if request.method == 'POST' and request.FILES.get('bdf_file_presupuesto'):
        bdf_file = request.FILES['bdf_file_presupuesto']

        if not bdf_file.name.endswith('.DBF'):
            return HttpResponse("Por favor sube un archivo .dbf válido para Presupuesto.")

        fs = FileSystemStorage(location='temp/')
        filename = fs.save(bdf_file.name, bdf_file)
        filepath = fs.path(filename)

        processed_count = 0
        created_count = 0
        updated_count = 0
        error_rows = []

        try:
            table = DBF(filepath, encoding='latin1')
            current_year = datetime.now().year

            for record in table:
                try:
                    nroparti = str(record['NROPARTI']).strip()

                    codigo = int(nroparti)
                    print(f"NROPARTI original: {record['NROPARTI']}, procesado: '{nroparti}', primer caracter: '{nroparti[0]}'")


                    # SECRETARIA según primer número
                    secretaria = SECRETARIA_MAP.get(nroparti[0], 'Otros')

                    # DIRECCION según primeros 2 números
                    direccion = DIRECCION_MAP.get(nroparti[:2], 'No definida')

                    # TIPO según tercer número
                    tipo = TIPO_MAP.get(nroparti[2], 'No definido')

                    # Cálculos
                    credito_actual = clean_and_convert(record['PRESUP'])
                    reestructuras = clean_and_convert(record['REESTR'])
                    compromiso = clean_and_convert(record['COMPRO'])
                    disponible = credito_actual + reestructuras - compromiso

                    defaults_data = {
                        'secretaria': secretaria,
                        'direccion': direccion,
                        'tipo': tipo,
                        'nombre': None,
                        'credito_actual': credito_actual,
                        'reestructuras': reestructuras,
                        'compromiso': compromiso,
                        'disponible': disponible,
                    }

                    obj, created = Presupuesto.objects.update_or_create(
                        codigo=codigo,
                        año=current_year,
                        defaults=defaults_data
                    )

                    processed_count += 1
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    error_rows.append({'data': dict(record), 'error': str(e)})
                    continue

            fs.delete(filename)

            summary_message = (
                f"Archivo .dbf de Presupuesto procesado: <br>"
                f"Total de filas procesadas: {processed_count}.<br>"
                f"Registros creados: {created_count}.<br>"
                f"Registros actualizados: {updated_count}.<br>"
                f"Filas con errores: {len(error_rows)}."
            )
            if error_rows:
                summary_message += "<br><br>Errores en primeras filas:<br>"
                for err in error_rows[:5]:
                    summary_message += f"{err['error']} - Datos: {err['data']}<br>"

            return HttpResponse(summary_message)

        except Exception as e:
            fs.delete(filename)
            return HttpResponse(f"Error procesando archivo DBF: {e}")

    return render(request, 'upload_csv.html')


def upload_movigast_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file_movigast'):
        csv_file = request.FILES['csv_file_movigast']

        if not csv_file.name.lower().endswith('.csv'):
            return HttpResponse("Por favor sube un archivo .csv válido para MoviGast.")

        fs = FileSystemStorage(location='temp/')
        filename = fs.save(csv_file.name, csv_file)
        filepath = fs.path(filename)

        try:
            df = pd.read_csv(filepath, encoding='latin1', sep=';', low_memory=False)

            # Normalizar nombres de columnas
            df.columns = df.columns.str.strip().str.upper()

            # Guarda una copia de las fechas originales como texto
            original_dates = df['FECHAREG'].copy()

            # Convierte a datetime
            df['FECHAREG'] = pd.to_datetime(df['FECHAREG'], dayfirst=True, errors='coerce')
            mes_actual = 7  # Julio (ajustar si se usa dinámico)

            filas_con_fechas_futuras = df[df['FECHAREG'].dt.month > mes_actual]
            if not filas_con_fechas_futuras.empty:
                print("--------------------------------------------------------------------")
                print(f"¡ATENCIÓN! Se encontraron {len(filas_con_fechas_futuras)} filas con fechas futuras.")
                print(filas_con_fechas_futuras[[
                    'FECHAREG', 
                    'TRAMITE', 
                    'IMPORTE'
                ]].head(10))
                print("--------------------------------------------------------------------")

            filas_con_error_fecha = df[df['FECHAREG'].isnull()]
            if not filas_con_error_fecha.empty:
                print("--- ¡ATENCIÓN! Fechas inválidas encontradas ---")
                print(f"Total con error: {len(filas_con_error_fecha)}")
                print(original_dates.loc[filas_con_error_fecha.index].head())
                print("----------------------------------------------------------")
            else:
                print("No se encontraron problemas con FECHAREG.")

            # Filtro por año 2025
            df = df[df['FECHAREG'].dt.year == 2025]

            # Filtrar por ETAPA3 == 1
            # Filtrar por ETAPA3 == 1
            if 'ETAPA3' in df.columns:
                df['ETAPA3'] = pd.to_numeric(df['ETAPA3'], errors='coerce')
                df = df[df['ETAPA3'] == 1]


            filas_filtradas = len(df)
            if filas_filtradas == 0:
                fs.delete(filename)
                return HttpResponse("No se encontraron registros válidos con FECHAREG en 2025 y ETAPA3 = 1.")

            # Preparar campos
            df['NROPARTI'] = df['NROPARTI'].astype(str).str.zfill(4)
            df['direccion'] = df['NROPARTI'].str[:2]
            df['gasto'] = df['NROPARTI'].str[2:4]
            df['mes'] = df['FECHAREG'].dt.month
            df['año'] = df['FECHAREG'].dt.year

            if 'IMPORTE' not in df.columns:
                fs.delete(filename)
                return HttpResponse("No se encontró la columna 'IMPORTE' en el archivo CSV.")

            # Limpiar importe
            df['IMPORTE'] = (
                df['IMPORTE']
                .astype(str)
                .str.replace(r'[^\d,.-]', '', regex=True)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
            )
            df['importe'] = pd.to_numeric(df['IMPORTE'], errors='coerce').fillna(0)

            # Actividad
            if 'PROGRAMA' in df.columns:
                df['actividad'] = df['PROGRAMA'].fillna(0).astype(int).astype(str)
            else:
                df['actividad'] = '0'

            # Agrupar por claves
            df_grouped = df.groupby(['direccion', 'gasto', 'mes', 'año', 'actividad'], as_index=False)['importe'].sum()

            created_count = 0
            updated_count = 0

            for _, row in df_grouped.iterrows():
                lookup_fields = {
                    'direccion': row['direccion'],
                    'gasto': row['gasto'],
                    'mes': int(row['mes']),
                    'año': int(row['año']),
                    'actividad': row['actividad']
                }

                defaults_data = {
                    'importe': Decimal(str(row['importe']))
                }

                obj, created = MoviGast.objects.update_or_create(
                    **lookup_fields,
                    defaults=defaults_data
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            fs.delete(filename)

            summary_message = (
                f"✅ Archivo CSV de MoviGast procesado:<br>"
                f"Filas válidas del año 2025 y ETAPA3=1: {filas_filtradas}.<br>"
                f"Registros creados: {created_count}.<br>"
                f"Registros actualizados: {updated_count}."
            )
            return HttpResponse(summary_message)

        except Exception as e:
            fs.delete(filename)
            return HttpResponse(f"❌ Error procesando archivo CSV: {e}")

    return render(request, 'upload-movigast.html')


def upload_reference_csv(request):
    """
    Vista unificada para cargar archivos CSV para los modelos de referencia.
    """
    model_map = {
        'secretaria_csv': Secretaria,
        'direccion_csv': Direccion,
        'actividad_csv': Actividad,
    }

    if request.method == 'POST':
        errores = []
        for input_name, model in model_map.items():
            csv_file = request.FILES.get(input_name)
            if csv_file:
                if not csv_file.name.lower().endswith('.csv'):
                    errores.append(f"Archivo de {model._meta.verbose_name} no es un CSV válido.")
                    continue

                try:
                    df = pd.read_csv(csv_file, sep=';', encoding='cp1252', dtype=str)
                    df.columns = df.columns.str.strip().str.upper()

                    if 'CODE' not in df.columns or 'DESC' not in df.columns:
                        errores.append(f"Archivo de {model._meta.verbose_name} no contiene columnas 'CODE' y 'DESC'.")
                        continue

                    df.dropna(subset=['CODE'], inplace=True)
                    df['CODE'] = df['CODE'].str.strip()
                    df['DESC'] = df['DESC'].str.strip()

                    for _, row in df.iterrows():
                        if row['CODE']:
                            model.objects.update_or_create(
                                code=row['CODE'],
                                defaults={'desc': row['DESC']}
                            )
                except Exception as e:
                    errores.append(f"Error procesando {model._meta.verbose_name}: {e}")

        if errores:
            return render(request, 'cargar-csv/upload_reference.html', {
                'errores': errores,
                'exito': False
            })
        else:
            return render(request, 'cargar-csv/upload_reference.html', {
                'exito': True
            })

    return render(request, 'cargar-csv/upload_reference.html')