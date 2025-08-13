from django import template

register = template.Library()

@register.filter
def split(value, separator):
    """Split string by separator"""
    if value:
        return [item.strip() for item in value.split(separator) if item.strip()]
    return []
