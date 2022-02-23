from .models import *
from django import forms
import re

class Useraddrf(forms.ModelForm):
    class Meta:
        model=Useraddr
        fields=['saddr']

class Userprofilef(forms.ModelForm):
    uimage=forms.ImageField(widget=forms.FileInput,)
    class Meta:
        model=Userprofile
        fields=['uimage']
