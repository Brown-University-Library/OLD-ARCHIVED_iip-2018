from django import template
from django.template.defaultfilters import stringfilter
import re
from iip_search_app import forms
import requests
import xml.etree.ElementTree as ET


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

vocab_request = requests.get("http://cds.library.brown.edu/projects/iip/include_taxonomies.xml")
vocab = ET.fromstring(vocab_request.content)
vocab_dict = dict([(element.attrib.values()[0], element.find('{http://www.tei-c.org/ns/1.0}catDesc').text) for element in vocab.findall('{http://www.tei-c.org/ns/1.0}category')])

@register.filter(name='vocabSort')
def vocabSort(values):
    return sorted(values, key=lambda x: vocab_dict[x[0]].lower() if x[0] in vocab_dict else x[0].lower())