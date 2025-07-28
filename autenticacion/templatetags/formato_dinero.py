from django import template

register = template.Library()

@register.filter
def formato_dinero(valor):
    if valor is None:
        return "0,00"
    return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")