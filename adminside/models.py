from django.utils import timezone
from django.db import models
from django.db.models.deletion import CASCADE


# Create your models here.
class Category(models.Model):
    cat_name=models.CharField(max_length=30,unique=True)
    offer=models.IntegerField(default=0)

    def __str__(self):
        return self.cat_name

class Product(models.Model):
    pro_name=models.CharField(max_length=100,unique=True )
    category=models.ForeignKey(Category,on_delete=CASCADE)
    price=models.FloatField()
    finalprice=models.FloatField(default=0)
    img1=models.ImageField(upload_to='productimage/',blank=True,null=False)
    img2=models.ImageField(upload_to='productimage/',blank=True,null=False)
    img3=models.ImageField(upload_to='productimage/',blank=True,null=False)
    desc=models.TextField(max_length=500)
    offer=models.IntegerField(default=0)
    stock=models.IntegerField()
    quantity=models.IntegerField()
    date=models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.pro_name

class Coupon(models.Model):
    coupon_code=models.CharField(max_length=50,unique=True)
    offer=models.IntegerField(default=0)

    def __str__(self):
        return self.coupon_code