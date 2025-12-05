"""
Template tags para el sistema de planes de mejoramiento
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def estado_badge(estado):
    """Retorna la clase CSS para el badge según el estado del plan"""
    estado_classes = {
        'BORRADOR': 'badge-estado-borrador',
        'ENVIADO': 'badge-estado-enviado',
        'FIRMADO_ENVIADO': 'badge-estado-firmado-enviado',
        'EN_REVISION': 'badge-estado-en-revision',
        'ESPERANDO_APROBACION': 'badge-estado-esperando-aprobacion',
        'SOLICITUD_AJUSTES': 'badge-estado-solicitud-ajustes',
        'REQUIERE_AJUSTES': 'badge-estado-requiere-ajustes',
        'DOCUMENTOS_REEVALUADOS': 'badge-estado-documentos-reevaluados',
        'APROBADO': 'badge-estado-aprobado',
        'RECHAZADO': 'badge-estado-rechazado',
    }
    return estado_classes.get(estado, 'badge-secondary')


@register.filter
def puntaje_badge(puntaje):
    """Retorna la clase CSS para el badge según el puntaje (Parametrización ITCO-ISA)"""
    try:
        puntaje = int(puntaje)
        if puntaje >= 80:
            return 'puntaje-satisfactorio'
        elif puntaje >= 60:
            return 'puntaje-aceptable'
        else:
            return 'puntaje-critico'
    except (ValueError, TypeError):
        return 'puntaje-aceptable'


@register.filter
def puntaje_color(puntaje):
    """Retorna el color para mostrar el puntaje (Parametrización ITCO-ISA)"""
    try:
        puntaje = int(puntaje)
        if puntaje >= 80:
            return 'text-success'
        elif puntaje >= 60:
            return 'text-warning'
        else:
            return 'text-danger'
    except (ValueError, TypeError):
        return 'text-secondary'


@register.simple_tag
def render_estado_badge(plan):
    """Renderiza un badge con el estado del plan"""
    if hasattr(plan, 'estado'):
        estado = plan.estado
        estado_display = plan.get_estado_display()
    else:
        return ''
    
    css_class = estado_badge(estado)
    html = f'<span class="badge badge-estado {css_class}">{estado_display}</span>'
    return mark_safe(html)


@register.simple_tag
def render_puntaje_badge(puntaje):
    """Renderiza un badge con el puntaje de la evaluación"""
    css_class = puntaje_badge(puntaje)
    html = f'<span class="puntaje-badge {css_class}">{puntaje}/100</span>'
    return mark_safe(html)


@register.filter
def multiply(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """Calcula el porcentaje de un valor sobre el total"""
    try:
        if total == 0:
            return 0
        return int((float(value) / float(total)) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def days_until(date_value):
    """Calcula los días hasta una fecha"""
    from datetime import date
    if not date_value:
        return None

    if isinstance(date_value, str):
        from datetime import datetime
        date_value = datetime.strptime(date_value, '%Y-%m-%d').date()

    delta = date_value - date.today()
    return delta.days


@register.filter
def split(value, separator):
    """Divide una cadena por un separador"""
    if value:
        return value.split(separator)
    return []


@register.filter
def add_days(date_value, days):
    """Suma días a una fecha"""
    from datetime import timedelta, datetime
    if not date_value:
        return None

    try:
        # Convertir días a entero
        days = int(days)

        # Si es string, convertir a datetime
        if isinstance(date_value, str):
            date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
        # Si es datetime, obtener solo la fecha
        elif hasattr(date_value, 'date'):
            date_value = date_value.date()

        # Sumar los días
        return date_value + timedelta(days=days)
    except (ValueError, TypeError):
        return date_value