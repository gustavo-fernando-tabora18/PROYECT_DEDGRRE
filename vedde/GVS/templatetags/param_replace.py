from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    params = context['request'].GET.copy()
    for key, value in kwargs.items():
        if value:
            params[key] = value
        else:
            params.pop(key, None)
    return params.urlencode()