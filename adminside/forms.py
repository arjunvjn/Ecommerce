from .models import *
from django import forms
import re

class Productf(forms.ModelForm):
    img1=forms.ImageField(widget=forms.FileInput,)
    img2=forms.ImageField(widget=forms.FileInput,)
    img3=forms.ImageField(widget=forms.FileInput,)
    class Meta:
        model=Product
        exclude = ('offer','date','finalprice')

    def clean(self):
        cleaned_data=super(Productf,self).clean()
        quantity=cleaned_data.get("quantity")
        stock=cleaned_data.get("stock")
        price=cleaned_data.get("price")
        
        if not re.match(r"^[+-]?[0-9]+$",str(stock)):
            self.add_error('stock',"Stock must be a integer")
        elif stock < 0:
            self.add_error('stock',"Stock must be greater than zero")
        if not re.match(r"^[+-]?[0-9]+$",str(quantity)):
            self.add_error('quantity',"Quantity must be a integer")
        elif quantity < 0:
            self.add_error('quantity',"Quantity must be greater than zero")
        if not re.match(r"^[+-]?[0-9]+[.]?[0-9]*$",str(price)):
            self.add_error('price',"Price must be a float")
        elif price<0:
            self.add_error('price',"Price must be greater than zero")
        return cleaned_data