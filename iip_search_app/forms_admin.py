from django import forms
from pagedown.widgets import AdminPagedownWidget
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from .models import StaticPage
from .widgets import AddAnotherWidgetWrapper


# class AdminBiographyForm(forms.ModelForm):
#     bio = forms.CharField(widget=AdminPagedownWidget())

#     class Meta:
#         model = Biography
#         fields = ('name', 'trp_id', 'alternate_names', 'external_id', 'birth_date', 'death_date', 'roles', 'bio')



class AdminStaticPageForm(forms.ModelForm):
    content = forms.CharField(widget=AdminPagedownWidget())

    class Meta:
        model = StaticPage
        fields = ( 'title', 'content' )
