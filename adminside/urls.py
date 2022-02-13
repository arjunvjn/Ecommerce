from django.urls import path
from . import views

urlpatterns=[
    path('',views.login,name='login'),
    path('home',views.home,name="home"),
    path('user',views.user,name='user'),
    path('product',views.product,name='product'),
    path('category',views.category,name='category'),
    path('catadd',views.catadd,name='catadd'),
    path('catedit/<id>',views.catedit,name='catedit'),
    path('catdel/<id>',views.catdel,name='catdel'),
    path('proadd',views.proadd,name='proadd'),
    path('proedit/<id>',views.proedit,name='proedit'),
    path('prodel/<id>',views.prodel,name='prodel'),
    path('userstat/<id>',views.userstat,name='userstat'),
    path('adminlogout',views.adminlogout,name='adminlogout'),
    path('orderman',views.order,name='orderman'),
    path('astat',views.cancelstat,name='astat'),
    path('ostat',views.deliverystat,name='ostat'),
    path('offerpro',views.offerpro,name='offerpro'),
    path('offercat',views.offercat,name='offercat'),
    path('offer_pro_edit/<id>',views.offer_pro_edit,name='offer_pro_edit'),
    path('offer_cat_edit/<id>',views.offer_cat_edit,name='offer_cat_edit'),
    path('offercoup',views.offercoup,name='offercoup'),
    path('coupadd',views.coupadd,name='coupadd'),
    path('coupedit/<id>',views.coupedit,name='coupedit'),
    path('coupdel/<id>',views.coupdel,name='coupdel'),
    path('sales',views.sales,name='sales'),
    path('sales_search',views.sales_search,name='sales_search'),
    path('export_excel',views.export_excel,name='export_excel'),
    path('search_pro',views.search_pro,name='search_pro'),
    path('search_cat',views.search_cat,name='search_cat')
]