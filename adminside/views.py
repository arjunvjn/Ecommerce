import datetime
from django.shortcuts import redirect, render
from django.contrib.auth.models import auth, User
from landing.models import Userprofile, Order
from .models import *
from .forms import Productf
from django.views.decorators.cache import never_cache
from django.http.response import JsonResponse, HttpResponse
from django.db.models import Q
from django.db.models import Sum, Count
import xlwt
from django.core.paginator import Paginator
# Create your views here.

# Admin login
@never_cache
def login(request):
    if request.user.is_authenticated:
        return redirect('/loginadmin/home')
    elif request.method == "POST":
        uname = request.POST['uname']
        psw = request.POST['psw']
        user = auth.authenticate(username=uname, password=psw)
        if user and user.is_superuser:
            auth.login(request, user)
            return redirect('/loginadmin/home')
        else:
            return render(request, 'adminside/adminlogin.html', {'err': "Invalid Credentials"})
    else:
        return render(request, 'adminside/adminlogin.html')

# Admin home
@never_cache
def home(request):
    if request.user.is_authenticated:
        order = Order.objects.all()
        # To get no. of orders made in COD
        cpay = order.filter(Q(pay='COD') & ~Q(
            status__in=['Returned', 'Cancelled'])).count()
        # To get no. of orders made in Razorpay
        rpay = order.filter(Q(pay='Razorpay') & ~Q(status__in=[
                            'Returned', 'Cancelled'])).count()
        # To get no. of orders made in Paypal
        ppay = order.filter(Q(pay='Paypal') & ~Q(status__in=[
                            'Returned', 'Cancelled'])).count()
        # To get no. of orders placed
        pstatus = order.filter(status='Order Placed').count()
        # To get no. of orders shipped
        sstatus = order.filter(status='Shipped').count()
        # To get no. of orders delivered
        dstatus = order.filter(status='Delivered').count()
        user = Userprofile.objects.all().count()
        pro = Product.objects.all()
        cpro = pro.count()
        # To get the most selling products
        spro = Order.objects.exclude(status__in=['Returned', 'Cancelled']).values('pro').annotate(
            pcount=Sum('qty')).order_by('-pcount')[:5]
        prol = []
        vall = []
        for i in spro:
            prod = Product.objects.get(id=i['pro'])
            prol.append(prod.pro_name)
            vall.append(i['pcount'])
        # To get the income
        rev = order.filter(Q(Q(pay__in=['Paypal', 'Razorpay']) & ~Q(status__in=['Returned', 'Cancelled'])) | Q(
            Q(pay='COD') & Q(status='Delivered'))).aggregate(Sum('sub_tot'))
        # To get the no. of products buyed on each day  
        dsale = Order.objects.exclude(status__in=['Returned', 'Cancelled']).values('date__date').annotate(
            pcount=Count('id')).order_by('date__date')[:7]  
        dayl = []
        coul = []
        for i in dsale:
            dayl.append(i['date__date'])
            coul.append(i['pcount'])
        context = {
            'cpay': cpay,
            'rpay': rpay,
            'ppay': ppay,
            'user': user,
            'pro': cpro,
            'pstatus': pstatus,
            'sstatus': sstatus,
            'dstatus': dstatus,
            'rev': rev['sub_tot__sum'],
            'prol': prol,
            'vall': vall,
            'dayl': dayl,
            'coul': coul
        }
        return render(request, 'adminside/adminhome.html', context)
    else:
        return redirect('/loginadmin')

# View user table
@never_cache
def user(request):
    if request.user.is_authenticated:
        usr = Userprofile.objects.all()
        return render(request, 'adminside/useradmin.html', {'user': usr})
    else:
        return redirect('/loginadmin')

# View category table
@never_cache
def category(request):
    if request.user.is_authenticated:
        cat = Category.objects.all()
        return render(request, 'adminside/catadmin.html', {'cat': cat})
    else:
        return redirect('/loginadmin')

# To add category
@never_cache
def catadd(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            cat = request.POST['cat']
            if Category.objects.filter(cat_name=cat).exists():
                context = {
                    'err': "Category already exists",
                    'url': '/loginadmin/catadd'
                }
                return render(request, 'adminside/catadd.html', context)
            else:
                new_cat = Category.objects.create(cat_name=cat, offer=0)
                new_cat.save()
                return redirect('/loginadmin/category')
        else:
            context = {
                'url': '/loginadmin/catadd'
            }
            return render(request, 'adminside/catadd.html', context)
    else:
        return redirect('/loginadmin')

# To edit category
@never_cache
def catedit(request, id=-1):
    if request.user.is_authenticated:
        if id == -1:
            return redirect('/loginadmin/category')
        else:
            ocat = Category.objects.get(pk=id)
            if request.method == 'POST':
                cat = request.POST['cat']
                if Category.objects.filter(cat_name=cat).exists() and ocat.cat_name != cat:
                    context = {
                        'err': "Category already exists",
                        'url': '/loginadmin/catedit/'+str(id),
                        'name': ocat.cat_name
                    }
                    return render(request, 'adminside/catadd.html', context)
                else:
                    ocat.cat_name = cat
                    ocat.save()
                    return redirect('/loginadmin/category')
            else:
                context = {
                    'name': ocat.cat_name,
                    'url': '/loginadmin/catedit/'+str(id)
                }
                return render(request, 'adminside/catadd.html', context)
    else:
        return redirect('/loginadmin')

# To delete category
@never_cache
def catdel(request, id=-1):
    if request.user.is_authenticated:
        if id == -1:
            return redirect('/loginadmin/category')
        else:
            ocat = Category.objects.get(pk=id)
            ocat.delete()
            return redirect('/loginadmin/category')
    else:
        return redirect('/loginadmin')

# View product table
@never_cache
def product(request):
    if request.user.is_authenticated:
        pro = Product.objects.all()
        return render(request, 'adminside/proadmin.html', {'pro': pro})
    else:
        return redirect('/loginadmin')

# To add product
@never_cache
def proadd(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = Productf(request.POST, request.FILES)
            if form.is_valid():
                pro = form.save(commit=False)
                # To set value to finalprice field
                if pro.category.offer > 0:           
                    pro.finalprice = pro.price - \
                        (pro.price*pro.category.offer/100)
                else:
                    pro.finalprice = form.cleaned_data['price']
                pro.save()
                return redirect('/loginadmin/product')
            else:
                return render(request, 'adminside/proadd.html', {'form': form, 'url': '/loginadmin/proadd'})
        else:
            form = Productf()
            return render(request, 'adminside/proadd.html', {'form': form, 'url': '/loginadmin/proadd'})
    else:
        return redirect('/loginadmin')

# To edit product
@never_cache
def proedit(request, id=-1):
    if request.user.is_authenticated:
        if id == -1:
            return redirect('/loginadmin/product')
        else:
            pro = Product.objects.get(pk=id)
            form = Productf(request.POST or None,
                            request.FILES or None, instance=pro)
            if request.method == 'POST':
                if form.is_valid():
                    form.save()
                    # To set value to finalprice field
                    if pro.offer >= pro.category.offer:           
                        pro.finalprice = pro.price-(pro.price*pro.offer/100)
                    else:
                        pro.finalprice = pro.price - \
                            (pro.price*pro.category.offer/100)
                    pro.save()
                    return redirect('/loginadmin/product')
                else:
                    context = {
                        'form': form,
                        'url': '/loginadmin/proedit/'+str(id),
                        'pro': pro
                    }
                    return render(request, 'adminside/proadd.html', context)
            else:
                context = {
                    'form': form,
                    'url': '/loginadmin/proedit/'+str(id),
                    'pro': pro
                }
                return render(request, 'adminside/proadd.html', context)
    else:
        return redirect('/loginadmin')

# To delete product
@never_cache
def prodel(request, id=-1):
    if request.user.is_authenticated:
        if id == -1:
            return redirect('/loginadmin/product')
        else:
            pro = Product.objects.get(pk=id)
            pro.delete()
            return redirect('/loginadmin/product')
    else:
        return redirect('/loginadmin')

# To block or unblock user
@never_cache
def userstat(request, id=-1):
    if request.user.is_authenticated:
        if id == -1:
            return redirect('/loginadmin/user')
        else:
            usr = Userprofile.objects.get(pk=id)
            user = User.objects.get(pk=usr.user.id)
            user.is_active = not(user.is_active)
            user.save()
            if request.session.has_key('login'):
                if user.username == request.session['login']:
                    del request.session['login']
            return redirect('/loginadmin/user')
    else:
        return redirect('/loginadmin')

# When admin logout
@never_cache
def adminlogout(request):
    if request.user.is_authenticated:
        auth.logout(request)
        return redirect('/loginadmin')
    else:
        return redirect('/loginadmin')

# To load Order page
@never_cache
def order(request):
    if request.user.is_authenticated:
        ord = Order.objects.all().order_by('-date')
        page = request.GET.get('page', 1)

        paginator = Paginator(ord, 5)
        try:
            order = paginator.page(page)
        except PageNotAnInteger:
            order = paginator.page(1)
        except EmptyPage:
            order = paginator.page(paginator.num_pages)
        return render(request, 'adminside/orderadmin.html', {'ord': order})
    else:
        return redirect('/loginadmin')

# To change the delivery status when admin click on status
def deliverystat(request):
    if request.method == 'GET':
        id = int(request.GET['oid'])
        order = Order.objects.get(id=id)
        if order.status == 'Order Placed':
            order.status = 'Shipped'
        elif order.status == 'Shipped':
            order.status = 'Delivered'
        order.save()
        data = {
            'stat': order.status
        }
        return JsonResponse(data)

# To change the delivery status when admin cancel order
def cancelstat(request):
    if request.method == 'GET':
        id = int(request.GET['oid'])
        order = Order.objects.get(id=id)
        order.status = 'Cancelled'
        pro = Product.objects.get(id=order.pro.id)
        pro.stock += order.qty
        pro.save()
        order.save()
        data = {
            'stat': order.status
        }
        return JsonResponse(data)

# To display the product offer page
@never_cache
def offerpro(request):
    if request.user.is_authenticated:
        pro = Product.objects.all()
        return render(request, 'adminside/offerpro.html', {'pro': pro})
    else:
        return redirect('/loginadmin')

# To display the category offer page
@never_cache
def offercat(request):
    if request.user.is_authenticated:
        cat = Category.objects.all()
        return render(request, 'adminside/offercat.html', {'cat': cat})
    else:
        return redirect('/loginadmin')

# To display the coupon offer page
@never_cache
def offercoup(request):
    if request.user.is_authenticated:
        coup = Coupon.objects.all()
        return render(request, 'adminside/offercoup.html', {'coup': coup})
    else:
        return redirect('/loginadmin')

# For adding coupon
@never_cache
def coupadd(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            coup = request.POST['ccode']
            offer = int(request.POST['offer'])
            if Coupon.objects.filter(coupon_code=coup).exists():
                context = {
                    'err': "Coupon already exists",
                    'url': '/loginadmin/coupadd'
                }
                return render(request, 'adminside/coupadd.html', context)
            else:
                new_coup = Coupon.objects.create(coupon_code=coup, offer=offer)
                new_coup.save()
                return redirect('/loginadmin/offercoup')
        else:
            context = {
                'url': '/loginadmin/coupadd'
            }
            return render(request, 'adminside/coupadd.html', context)
    else:
        return redirect('/loginadmin')

# For editing coupon
@never_cache
def coupedit(request, id=-1):
    if request.user.is_authenticated:
        if id == -1:
            return redirect('/loginadmin/offercoup')
        else:
            coupon = Coupon.objects.get(pk=id)
            if request.method == 'POST':
                coup = request.POST['ccode']
                offer = int(request.POST['offer'])
                if Coupon.objects.filter(coupon_code=coup).exists() and coupon.coupon_code != coup:
                    context = {
                        'err': "Coupon already exists",
                        'url': '/loginadmin/coupedit/'+str(id),
                        'name': coupon.coupon_code
                    }
                    return render(request, 'adminside/coupadd.html', context)
                else:
                    coupon.coupon_code = coup
                    coupon.offer = offer
                    coupon.save()
                    return redirect('/loginadmin/offercoup')
            else:
                context = {
                    'name': coupon.coupon_code,
                    'val': coupon.offer,
                    'url': '/loginadmin/coupedit/'+str(id)
                }
                return render(request, 'adminside/coupadd.html', context)
    else:
        return redirect('/loginadmin')

# To delete coupon
@never_cache
def coupdel(request, id=-1):
    if request.user.is_authenticated:
        if id == -1:
            return redirect('/loginadmin/offercoup')
        else:
            coup = Coupon.objects.get(pk=id)
            coup.delete()
            return redirect('/loginadmin/offercoup')
    else:
        return redirect('/loginadmin')

# For editing product offer
@never_cache
def offer_pro_edit(request, id=-1):
    if request.user.is_authenticated:
        pro = Product.objects.get(id=id)
        if id == -1:
            return redirect('/loginadmin')
        elif request.method == 'POST':
            offer = int(request.POST['offer'])
            pro.offer = offer
            # To set value to finalprice field
            if pro.offer >= pro.category.offer:           
                pro.finalprice = pro.price-(pro.price*pro.offer/100)
            else:
                pro.finalprice = pro.price-(pro.price*pro.category.offer/100)
            pro.save()
            return redirect('/loginadmin/offerpro')
        else:
            return render(request, 'adminside/offeredit.html', {'url': '/loginadmin/offer_pro_edit/'+str(id), 'val': pro.offer})
    else:
        return redirect('/loginadmin')

# For editing category offer
@never_cache
def offer_cat_edit(request, id=-1):
    if request.user.is_authenticated:
        cat = Category.objects.get(id=id)
        if id == -1:
            return redirect('/loginadmin')
        elif request.method == 'POST':
            offer = int(request.POST['offer'])
            cat.offer = offer
            cat.save()
            pro = Product.objects.filter(category=cat)
            # To set value to finalprice field
            for i in pro:                            
                if i.offer >= i.category.offer:
                    i.finalprice = i.price-(i.price*i.offer/100)
                elif i.offer < i.category.offer:
                    i.finalprice = i.price-(i.price*i.category.offer/100)
                i.save()
            return redirect('/loginadmin/offercat')
        else:
            return render(request, 'adminside/offeredit.html', {'url': '/loginadmin/offer_cat_edit/'+str(id), 'val': cat.offer})
    else:
        return redirect('/loginadmin')

# To display sales report
@never_cache
def sales(request):
    if request.user.is_authenticated:
        ord = Order.objects.all().order_by('-date')
        return render(request, 'adminside/salesreport.html', {'ord': ord})
    else:
        return redirect('/loginadmin')

# For searching sales based on date
@never_cache
def sales_search(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            fromdate = request.POST['from']
            to = request.POST['to']
            if to != '':
                setto = to.split('-')
                if (int(setto[2])+1) < 10:
                    setto[2] = '0'+str(int(setto[2])+1)
                else:
                    setto[2] = str(int(setto[2])+1)
                todate = '-'.join(setto)
            else:
                todate = ''
            request.session['fromdate'] = fromdate
            request.session['todate'] = todate
            if fromdate == '' and todate == '':
                ord = Order.objects.all().order_by('-date')
            elif fromdate == '':
                ord = Order.objects.filter(date__lt=todate).order_by('-date')
            elif todate == '':
                ord = Order.objects.filter(
                    date__gte=fromdate).order_by('-date')
            else:
                ord = Order.objects.filter(
                    date__range=[fromdate, todate]).order_by('-date')
            return render(request, 'adminside/salesreport.html', {'ord': ord})
    else:
        return redirect('/loginadmin')

# For exporting in excel format
@never_cache
def export_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Sales' + \
        str(datetime.datetime.now())+'.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Sales Report')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['Order Date', 'Order Id', 'Product Name', 'Quantity',
               'Payment Method', 'Address', 'Amount', 'Delivery Status']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    if request.session.has_key('fromdate'):
        fromdate = request.session['fromdate']
    else:
        fromdate = ''
    if request.session.has_key('todate'):
        todate = request.session['todate']
    else:
        todate = ''
    if fromdate == '' and todate == '':
        rows = Order.objects.all().values_list('date__date', 'order_uuid', 'pro', 'qty',
                                               'pay', 'addr', 'sub_tot', 'status').order_by('-date')
    elif fromdate == '':
        rows = Order.objects.filter(date__lt=todate).values_list(
            'date__date', 'order_uuid', 'pro', 'qty', 'pay', 'addr', 'sub_tot', 'status').order_by('-date')
    elif todate == '':
        rows = Order.objects.filter(date__gte=fromdate).values_list(
            'date__date', 'order_uuid', 'pro', 'qty', 'pay', 'addr', 'sub_tot', 'status').order_by('-date')
    else:
        rows = Order.objects.filter(date__range=[fromdate, todate]).values_list(
            'date__date', 'order_uuid', 'pro', 'qty', 'pay', 'addr', 'sub_tot', 'status').order_by('-date')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            if col_num == 2:
                pro = Product.objects.get(id=row[col_num])
                ws.write(row_num, col_num, str(pro.pro_name), font_style)
            else:
                ws.write(row_num, col_num, str(row[col_num]), font_style)
    wb.save(response)
    return response

# For searching product based on product name
@never_cache
def search_pro(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            pro = request.POST['pro']
            id = int(request.POST['sea'])
            prolist = Product.objects.filter(
                pro_name__icontains=pro).order_by('-date')
            if id == 0:
                return render(request, 'adminside/proadmin.html', {'pro': prolist})
            elif id == 1:
                return render(request, 'adminside/offerpro.html', {'pro': prolist})
            else:
                return redirect('/loginadmin')
        else:
            return redirect('/loginadmin')
    else:
        return redirect('/loginadmin')

# For searching category based on category name
@never_cache
def search_cat(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            cat = request.POST['cat']
            id = int(request.POST['sea'])
            catlist = Category.objects.filter(cat_name__icontains=cat)
            if id == 0:
                return render(request, 'adminside/catadmin.html', {'cat': catlist})
            elif id == 1:
                return render(request, 'adminside/offercat.html', {'cat': catlist})
            else:
                return redirect('/loginadmin')
        else:
            return redirect('/loginadmin')
    else:
        return redirect('/loginadmin')
