from django import template
from django.template.defaultfilters import stringfilter
import re
register = template.Library()

@register.filter(name='underscoreToSpace')
@stringfilter
def underscoreToSpace(value):
    return value.replace("_", " ")

@register.filter(name='cleanDates')
@stringfilter
def cleanDates(value):
    value = re.sub(r'-(\d+)', r' \1 BCE', value)
    value = re.sub(r'(\d+)\b(?!\sBCE)', r' \1 CE', value)
    return value
