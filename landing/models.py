from django.db import models
from django.db.models.deletion import CASCADE
from django.contrib.auth.models import User
from adminside.models import *
import uuid

# Create your models here.

class Userprofile(models.Model):
    user=models.OneToOneField(User,on_delete=CASCADE)
    number=models.CharField(max_length=11,unique=True,null=True)
    uimage=models.ImageField(upload_to='userimage',blank=True)

    def __str__(self):
        return self.number

class Cart(models.Model):
    user=models.ForeignKey(Userprofile,on_delete=CASCADE,null=True)
    guest=models.CharField(max_length=250,null=True)
    pro=models.ForeignKey(Product,on_delete=CASCADE)
    qty=models.IntegerField(default=1)
    sub_tot=models.FloatField()

    def __str__(self):
        return self.user.user.username

class Useraddr(models.Model):
    name=models.CharField(max_length=50)
    number=models.CharField(max_length=11)
    addr=models.TextField(max_length=500)
    city=models.CharField(max_length=50)
    pin=models.CharField(max_length=7)
    saddr=models.BooleanField(default=False)
    user=models.ForeignKey(Userprofile,on_delete=CASCADE)

    def __str__(self):
        return self.user.user.username

class Order(models.Model):
    order_uuid = models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    pro=models.ForeignKey(Product,on_delete=CASCADE)
    user=models.ForeignKey(Userprofile,on_delete=CASCADE)
    sub_tot=models.FloatField()
    qty=models.IntegerField()
    addr=models.TextField(max_length=800)
    pay=models.CharField(max_length=20)
    status=models.CharField(max_length=20)
    date=models.DateTimeField(default=timezone.now)
    coupon=models.ForeignKey(Coupon,on_delete=CASCADE,null=True)

    def __str__(self):
        return self.pro.pro_name