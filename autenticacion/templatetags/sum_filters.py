from django import template

register = template.Library()

@register.filter
def sum_field(lista, campo):
    try:
        return sum(float(item.get(campo, 0)) for item in lista if item.get(campo) is not None)
    except Exception:
        return 0
@register.filter
def get_item(dictionary, key):
    """
    Permite acceder a los valores de un diccionario con una clave variable en las plantillas de Django.
    Uso: {{ mi_diccionario|get_item:mi_clave }}
    """
    return dictionary.get(key)