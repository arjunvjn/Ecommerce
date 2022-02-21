from unicodedata import name
from django.urls import path,include
from . import views

urlpatterns=[
    path('',views.index,name="index"),
    path('signup',views.signup,name="signup"),
    path('signin',views.signin,name="signin"),
    path('otps',views.signin_num,name="otps"),
    path('otp',views.signin_otp,name="otp"),
    path('single/<id>',views.single,name="single"),
    path('category/<id>',views.category,name="category"),
    path('logout',views.logout,name='logout'),
    path('addcart',views.addtocart,name='addcart'),
    path('viewcart',views.viewcart,name='viewcart'),
    path('pluscart',views.pluscart,name='pluscart'),
    path('minuscart',views.minuscart,name='minuscart'),
    path('delcart',views.delcart,name='delcart'),
    path('setaddr',views.address,name='setaddr'),
    path('getaddr/<id>',views.getaddr,name='getaddr'),
    path('pcod/<id>/<value>',views.payment,name='pcod'),
    path('orders',views.orders,name='orders'),
    path('getnewaddr',views.getnewaddr,name='getnewaddr'),
    path('accounts/', include('allauth.urls')),
    path('social',views.social,name='social'),
    path('ustat',views.order_stat,name='ustat'),
    path('profile',views.profile,name='profile'),
    path('edituser',views.edituser,name='edituser'),
    path('change_pass',views.change_pass,name='change_pass'),
    path('deladdr/<id>',views.deladdr,name='deladdr'),
    path('coupon_apply',views.coupon_apply,name='coupon_apply'),
    path('search',views.search,name='search'),
    path('checkcart',views.checkcart,name='checkcart'),
    path('price_sort',views.price_sort,name='price_sort'),
    path('buy_now/<id>',views.buy_now,name='buy_now'),
    path('otp_resend',views.otp_resend,name='otp_resend'),
    path('invoice/<c>',views.invoice,name='invoice')
]