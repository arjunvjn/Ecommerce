from django.http.response import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.models import auth, User
from .models import *
from adminside.models import *
from django.views.decorators.cache import never_cache
import razorpay
from .exchange import RealTimeCurrencyConverter
from .forms import *
from decouple import config
from django.db.models import Sum
from .otp import *
# Create your views here.

pay_method = {1: 'COD', 2: 'Razorpay', 3: 'Paypal'}

# Function to move the cart from guest_user to logged_in user
def guest_to_user(request):
    name = request.session['login']
    usr = User.objects.get(username=name)
    user = Userprofile.objects.get(user=usr)
    if request.session.session_key:
        guest = request.session.session_key
        if Cart.objects.filter(guest=guest).exists():
            gcart = Cart.objects.filter(guest=guest)
            if Cart.objects.filter(user=user).exists():
                ucart = Cart.objects.filter(user=user)
                for i in ucart:
                    if gcart.filter(pro=i.pro).exists():
                        g = gcart.get(pro=i.pro)
                        i.qty += g.qty
                        i.save()
                        g.delete()
            gcart.update(user=user, guest='')


# Landing Page function
@never_cache
def index(request):
    if request.session.has_key('login'):
        user = request.session['login']
    else:
        user = None
    if request.session.has_key('buy_now'):
        del request.session['buy_now']
    # To get products whose stoke is greater than zero
    prod = Product.objects.filter(stock__gt=0)
    ca = Category.objects.all()
    cat=[]
    pro = []
    for i in ca:
        if Product.objects.filter(category=i).exists():
            pro.extend(prod.filter(category=i).order_by('-date')[:3])
            cat.append(i)
    context = {
        'pro': pro,
        'cat': cat,
        'user': user,
        'ca':ca
    }
    return render(request, 'landing/index.html', context)

# Signup function
@never_cache
def signup(request):
    if request.session.has_key('login'):
        return redirect('/')
    elif request.method == 'POST':
        User.objects.filter(is_active=False).delete()
        num = request.POST['num']
        uname = request.POST['uname']
        lname = request.POST['lname']
        fname = request.POST['fname']
        email = request.POST['email']
        psw = request.POST['pwd']
        if Userprofile.objects.filter(number=num).exists() or User.objects.filter(username=uname).exists() or User.objects.filter(email=email).exists():
            if Userprofile.objects.filter(number=num).exists():
                messages.info(request, "Phone number already exits")
            if User.objects.filter(username=uname).exists():
                messages.info(request, "Username already exits")
            if User.objects.filter(email=email).exists():
                messages.info(request, "Email Id already exits")
            return render(request, 'landing/signup.html')
        else:
            user = User.objects.create_user(
                first_name=fname, last_name=lname, email=email, username=uname, password=psw, is_active=False)
            user.save()
            uprofile = Userprofile.objects.create(
                user=user, number=num, uimage='userimage/user.png')
            uprofile.save()
            request.session['num'] = num
            if send(num):
                return render(request, 'landing/otp.html', {'url': '/otp'})
            else:
                messages.info(request, "Invalid Number")
                return render(request, 'landing/signup.html')
    else:
        return render(request, 'landing/signup.html')

# Signin with username function
@never_cache
def signin(request):
    if request.session.has_key('login'):
        return redirect('/')
    elif request.method == "POST":
        User.objects.filter(is_active=False).delete()
        uname = request.POST['user']
        psw = request.POST['psw']
        user = auth.authenticate(username=uname, password=psw)
        if user and (not user.is_superuser):
            request.session['login'] = user.username
            guest_to_user(request)
            return redirect('/')
        else:
            if User.objects.filter(username=uname).exists():
                usr = User.objects.get(username=uname)
                if not usr.is_active:
                    return render(request, 'landing/signin.html', {'err': "You have been Blocked"})
                else:
                    return render(request, 'landing/signin.html', {'err': "Invalid Credentials"})
            else:
                return render(request, 'landing/signin.html', {'err': "Invalid Credentials"})
    else:
        return render(request, 'landing/signin.html')

# Signin with number
@never_cache
def signin_num(request):
    if request.session.has_key('login'):
        return redirect('/')
    elif request.method == "POST":
        User.objects.filter(is_active=False).delete()
        num = request.POST['num']
        if Userprofile.objects.filter(number=num).exists():
            usr = Userprofile.objects.get(number=num)
            user = User.objects.get(id=usr.user.id)
            if user.is_active:
                if send(num):
                    request.session['num'] = num
                    return render(request, 'landing/otp.html', {'url': '/otp'})
                else:
                    return render(request, 'landing/signin.html', {'err': "Wrong Number"})
            else:
                return render(request, 'landing/signin.html', {'err': "Invalid User"})
        else:
            return render(request, 'landing/signin.html', {'err': "Invalid User"})
    else:
        return render(request, 'landing/signin.html')

# Signin with number OTP verification
@never_cache
def signin_otp(request):
    if request.session.has_key('login'):
        return redirect('/')
    elif request.session.has_key('num'):
        if request.method == 'POST':
            num = request.session['num']
            otp = request.POST['otp']
            if verify(otp, num) == "approved":
                del request.session['num']
                usr = Userprofile.objects.get(number=num)
                user = User.objects.get(id=usr.user.id)
                if not user.is_active:
                    user.is_active = True
                    user.save()
                request.session['login'] = usr.user.username
                guest_to_user(request)
                return redirect('/')
            else:
                return render(request, 'landing/otp.html', {'url': '/otp', 'err': "Wrong OTP"})
        else:
            return render(request, 'landing/signin.html',{'url': '/otp'})
    else:
        return render(request, 'landing/signin.html',{'url': '/otp'})

# Product detail function
@never_cache
def single(request, id=-1):
    if request.session.has_key('login'):
        user = request.session['login']
    else:
        user = None
    if request.session.has_key('buy_now'):
        del request.session['buy_now']
    if id == -1:
        return redirect('/')
    else:
        c = Category.objects.all()
        pro = Product.objects.get(pk=id)
        context = {
            'pro': pro,
            'user': user,
            'cat': c
        }
        return render(request, 'landing/single.html', context)

# Single Category function
@never_cache
def category(request, id=-1):
    if request.session.has_key('login'):
        user = request.session['login']
    else:
        user = None
    if request.session.has_key('buy_now'):
        del request.session['buy_now']
    if id == -1:
        return redirect('/')
    else:
        cat = Category.objects.get(pk=id)
        c = Category.objects.all()
        pro = Product.objects.filter(category=cat)
        context = {
            'pro': pro,
            'user': user,
            'cat': c,
            'cname': cat.cat_name
        }
        return render(request, 'landing/product.html', context)

# Logout function
@never_cache
def logout(request):
    if request.session.has_key('login'):
        del request.session['login']
        return redirect('/')
    else:
        return redirect('/')

# Function for Add to Cart button
def addtocart(request):
    f = 1
    if request.method == 'GET':
        id = int(request.GET['pid'])
        pro = Product.objects.get(pk=id)
        if request.session.has_key('login'):
            uname = request.session['login']
            user = User.objects.get(username=uname)
            usr = Userprofile.objects.get(user=user)
            if Cart.objects.filter(user=usr, pro=pro).exists():
                mycart = Cart.objects.get(user=usr, pro=pro)
            else:
                Cart.objects.create(
                    user=usr, pro=pro, sub_tot=pro.finalprice)
                data = {
                        'f': f
                    }
                return JsonResponse(data)
        else:
            if not request.session.session_key:
                request.session.create()
            sessioin_key = request.session.session_key
            if Cart.objects.filter(guest=sessioin_key, pro=pro).exists():
                mycart = Cart.objects.get(guest=sessioin_key, pro=pro)
            else:
                Cart.objects.create(
                    guest=sessioin_key, pro=pro, sub_tot=pro.finalprice)
                data = {
                        'f': f
                    }
                return JsonResponse(data)
        # add cart quantity if there is stock
        if mycart.qty < pro.stock: 
            mycart.qty += 1
            mycart.save()
        data = {
            'f': f
        }
        return JsonResponse(data)

# Cart page loading function
@never_cache
def viewcart(request):
    c = Category.objects.all()
    if request.session.has_key('login'):
        uname = request.session['login']
        user = User.objects.get(username=uname)
        usr = Userprofile.objects.get(user=user)
        # To check if there is product in cart
        if Cart.objects.filter(user=usr).exists():
            cart = Cart.objects.filter(user=usr)
        else:
            a = "Your cart is Empty"
            return render(request, 'landing/cart.html', {'err': a, 'cat': c, 'user': uname})
    else:
        uname=None
        if not request.session.session_key:
            request.session.create()
        sessioin_key = request.session.session_key
        # To check if there is product in cart
        if Cart.objects.filter(guest=sessioin_key).exists():
            cart = Cart.objects.filter(guest=sessioin_key)
        else:
            a = "Your cart is Empty"
            return render(request, 'landing/cart.html', {'err': a, 'cat': c, 'user': None})
    tot = 0
    for i in cart:
        i.sub_tot = i.qty*i.pro.finalprice
        tot += i.sub_tot
        i.save()                           
    context = {
                'cart': cart,
                'tot': tot,
                'err': None,
                'cat': c,
                'user': uname
            }
    return render(request, 'landing/cart.html', context)

# Function to increment cart count
def pluscart(request):
    if request.method == 'GET':
        id = int(request.GET['cid'])
        cart = Cart.objects.get(id=id)
        if request.session.has_key('login'):
            uname = request.session['login']
            user = User.objects.get(username=uname)
            usr = Userprofile.objects.get(user=user)
            tot = Cart.objects.filter(user=usr).aggregate(Sum('sub_tot'))
        else:
            sessioin_key = request.session.session_key
            tot = Cart.objects.filter(
                guest=sessioin_key).aggregate(Sum('sub_tot'))
        # add cart quantity if there is stock
        if cart.qty < cart.pro.stock:                         
            cart.qty += 1
            cart.sub_tot += cart.pro.finalprice
            cart.save()
            tot['sub_tot__sum'] += cart.pro.finalprice
            f = 0
        else:
            f = 1
        data = {
            'sub': cart.sub_tot,
            'qty': cart.qty,
            'total': tot['sub_tot__sum'],
            'f': f
        }
        return JsonResponse(data)

# Function to decrement cart count
def minuscart(request):
    if request.method == 'GET':
        id = int(request.GET['cid'])
        cart = Cart.objects.get(id=id)
        if request.session.has_key('login'):
            uname = request.session['login']
            user = User.objects.get(username=uname)
            usr = Userprofile.objects.get(user=user)
            tot = Cart.objects.filter(user=usr).aggregate(Sum('sub_tot'))
        else:
            sessioin_key = request.session.session_key
            tot = Cart.objects.filter(
                guest=sessioin_key).aggregate(Sum('sub_tot'))
        cart.qty -= 1
        cart.sub_tot -= cart.pro.finalprice
        cart.save()
        tot['sub_tot__sum'] -= cart.pro.finalprice
        data = {
            'sub': cart.sub_tot,
            'qty': cart.qty,
            'total': tot['sub_tot__sum']
        }
        return JsonResponse(data)

# Function to delete product from cart
def delcart(request):
    if request.method == 'GET':
        id = int(request.GET['cid'])
        cart = Cart.objects.get(id=id)
        if request.session.has_key('login'):
            uname = request.session['login']
            user = User.objects.get(username=uname)
            usr = Userprofile.objects.get(user=user)
            tot = Cart.objects.filter(user=usr).aggregate(Sum('sub_tot'))
        else:
            sessioin_key = request.session.session_key
            tot = Cart.objects.filter(
                guest=sessioin_key).aggregate(Sum('sub_tot'))
        tot['sub_tot__sum'] -= cart.sub_tot
        cart.delete()
        data = {

            'total': tot['sub_tot__sum']
        }
        return JsonResponse(data)

# Function to load address page
@never_cache
def address(request):
    if request.session.has_key('login'):
        uname = request.session['login']
        if request.session.has_key('coupon'):
            del request.session['coupon']
        user = User.objects.get(username=uname)
        usr = Userprofile.objects.get(user=user)
        if request.session.has_key('buy_now'):
            pro=Product.objects.filter(id=request.session['buy_now'])
            tot=pro[0].finalprice
            uaddr = Useraddr.objects.filter(user=usr)
            uaddr.filter(saddr=False).delete()
            form = Useraddrf()
            context = {
                'addr': uaddr,
                'form': form,
                'cat': pro,
                'user': uname,
                'tot': tot
            }
        else:
            cart = Cart.objects.filter(user=usr)
            c = Category.objects.all()
            tot = 0
            for i in cart:
                # To delete product from cart if cart quantity is less than product stock
                if i.qty > i.pro.stock:                   
                    i.delete()
                i.sub_tot = i.qty*i.pro.finalprice
                tot += i.sub_tot
                i.save()
            uaddr = Useraddr.objects.filter(user=usr)
            uaddr.filter(saddr=False).delete()
            form = Useraddrf()
            context = {
                'addr': uaddr,
                'form': form,
                'cat': c,
                'user': uname,
                'tot': tot
            }
        return render(request, 'landing/address.html', context)
    else:
        return redirect('/signin')

# Function to check cart product is available
@never_cache
def checkcart(request):
    if request.session.has_key('login'):
        if request.session.has_key('coupon'):
            del request.session['coupon']
        if request.session.has_key('buy_now'):
            del request.session['buy_now']
        uname = request.session['login']
        user = User.objects.get(username=uname)
        usr = Userprofile.objects.get(user=user)
        cart = Cart.objects.filter(user=usr)
        uaddr = Useraddr.objects.filter(user=usr)
        uaddr.filter(saddr=False).delete()
        pro = []
        for i in cart:
            if i.qty > i.pro.stock:
                pro.append(i.pro.id)
        if len(pro) > 0:
            if len(pro) == 1:
                p = Product.objects.get(id=pro[0])
                sp = p.pro_name
                f = 1
            else:
                prolist = Product.objects.filter(id__in=pro)
                proname = [p.pro_name for p in prolist]
                sp = ','.join(proname)
                f = 2
            data = {
                'f': f,
                'name': sp
            }
            return JsonResponse(data)
        else:
            return JsonResponse({'f': 0})
    else:
        return JsonResponse({'f': 3})


# Fuction for saved address and load payment page
@never_cache
def getaddr(request, id=-1):
    if request.session.has_key('login'):
        uname = request.session['login']
        user = User.objects.get(username=uname)
        usr = Userprofile.objects.get(user=user)
        uaddr = Useraddr.objects.filter(user=usr)
        uaddr.filter(saddr=False).delete()
        if request.session.has_key('buy_now'):
            pro=Product.objects.get(id=request.session['buy_now'])
            tot=pro.finalprice
        else:
            to=Cart.objects.filter(user=usr).aggregate(Sum('sub_tot'))
            tot=to['sub_tot__sum']
        if request.session.has_key('coupon'):
            coup=Coupon.objects.get(id=request.session['coupon'])
            tot-=(tot*coup.offer/100)
        c = Category.objects.all()
        if id != -1:
            client = razorpay.Client(
                auth=(config('KEY_ID'), config('KEY_SECRET')))
            rup = tot*100
            DATA = {
                "amount": rup,
                "currency": "INR",
                'payment_capture': '1'
            }
            payment = client.order.create(data=DATA)
            url = 'https://api.exchangerate-api.com/v4/latest/USD'
            converter = RealTimeCurrencyConverter(url)
            usd = converter.convert('INR', 'USD', tot)
            context = {
                'aid': id,
                'tot': tot,
                'payment': payment,
                'usr': user,
                'rupee': rup,
                'usd': usd,
                'cat': c,
                'user': uname
            }
            return render(request, 'landing/payment.html', context)
        else:
            return redirect('/')
    else:
        return redirect('/signin')

# Fuction for new address and load payment page
@never_cache
def getnewaddr(request):
    if request.session.has_key('login'):
        uname = request.session['login']
        user = User.objects.get(username=uname)
        usr = Userprofile.objects.get(user=user)
        uaddr = Useraddr.objects.filter(user=usr)
        uaddr.filter(saddr=False).delete()
        if request.session.has_key('buy_now'):
            pro=Product.objects.get(id=request.session['buy_now'])
            tot=pro.finalprice
        else:
            to=Cart.objects.filter(user=usr).aggregate(Sum('sub_tot'))
            tot=to['sub_tot__sum']
        if request.session.has_key('coupon'):
            coup=Coupon.objects.get(id=request.session['coupon'])
            tot-=(tot*coup.offer/100)
        c = Category.objects.all()
        if request.method == 'POST':
            form = Useraddrf(request.POST)
            if form.is_valid():
                usaddr = form.cleaned_data['saddr']
            name = request.POST['name']
            num = request.POST['number']
            addr = request.POST['addr']
            city = request.POST['city']
            pin = request.POST['pin']
            uaddr = Useraddr.objects.create(
                name=name, number=num, addr=addr, city=city, pin=pin, user=usr, saddr=usaddr)
            uaddr.save()
            client = razorpay.Client(
                auth=(config('KEY_ID'), config('KEY_SECRET')))
            rup = tot*100
            DATA = {
                "amount": rup,
                "currency": "INR",
                'payment_capture': '1'
            }
            payment = client.order.create(data=DATA)
            url = 'https://api.exchangerate-api.com/v4/latest/USD'
            converter = RealTimeCurrencyConverter(url)
            usd = converter.convert('INR', 'USD', tot)
            context = {
                'aid': uaddr.id,
                'tot': tot,
                'payment': payment,
                'usr': user,
                'rupee': rup,
                'usd': usd,
                'cat': c,
                'user': uname
            }
            return render(request, 'landing/payment.html', context)
        else:
            return redirect('/')
    else:
        return redirect('/signin')

# Fuction to place order when COD payment is made
@never_cache
def payment(request, id=-1, value=-1):
    global pay_method
    val = int(value)
    if request.session.has_key('login'):
        uname = request.session['login']
        user = User.objects.get(username=uname)
        usr = Userprofile.objects.get(user=user)
        if id == -1 or value == -1:
            return redirect('/')
        else:
            uaddr = Useraddr.objects.get(id=id)
            addr = uaddr.name+","+uaddr.number+","+uaddr.addr+","+uaddr.city+","+uaddr.pin
            c=0
            if request.session.has_key('buy_now'):
                pro=Product.objects.get(id=request.session['buy_now'])
                if request.session.has_key('coupon'):
                    cid = request.session['coupon']
                    coupon = Coupon.objects.get(id=cid)
                    pro.finalprice -= (pro.finalprice*coupon.offer/100)
                    order = Order.objects.create(pro=pro, user=usr, sub_tot=pro.finalprice, qty=1,
                                                    pay=pay_method[val], status="Order Placed", addr=addr, coupon=coupon)
                else:
                    order = Order.objects.create(
                            pro=pro, user=usr, sub_tot=pro.finalprice, qty=1, pay=pay_method[val], status="Order Placed", addr=addr)
                order.save()
                c+=1
                pro.stock-=1
                pro.save()
                del request.session['buy_now']
            else:
                cart = Cart.objects.filter(user=usr)
                for i in cart:
                    if request.session.has_key('coupon'):
                        cid = request.session['coupon']
                        coupon = Coupon.objects.get(id=cid)
                        i.sub_tot -= (i.sub_tot*coupon.offer/100)
                        i.save()
                        order = Order.objects.create(pro=i.pro, user=usr, sub_tot=i.sub_tot, qty=i.qty,
                                                    pay=pay_method[val], status="Order Placed", addr=addr, coupon=coupon)
                    else:
                        order = Order.objects.create(
                            pro=i.pro, user=usr, sub_tot=i.sub_tot, qty=i.qty, pay=pay_method[val], status="Order Placed", addr=addr)
                    order.save()
                    c+=1
                    cpro = Product.objects.get(id=i.pro.id)
                    cpro.stock -= i.qty
                    cpro.save()
                cart.delete()
            if request.session.has_key('coupon'):
                del request.session['coupon']
            if uaddr.saddr == False:
                uaddr.delete()
            return redirect('/invoice/'+str(c))
    else:
        return redirect('/signin')

# For Invoice
def invoice(request,c=-1):
    if c==-1:
        return redirect('/')
    else:
        c=int(c)
    if request.session.has_key('login'):
        uname = request.session['login']
        user = User.objects.get(username=uname)
        usr = Userprofile.objects.get(user=user)
        order=Order.objects.filter(user=usr).order_by('-date')[:c]
        addr=order[0].addr
        addrs = addr.split(',')
        aname = addrs[0]
        aaddr = addrs[2]
        acity = addrs[3]+","+addrs[4]
        aphone = addrs[1]
        tot=order.aggregate(Sum('sub_tot'))
        context={
            'name':aname,
            'addr':aaddr,
            'city':acity,
            'number':aphone,
            'tot':tot['sub_tot__sum'],
            'order':order
        }
        return render(request, 'landing/invoice.html', context)
    else:
        return redirect('/')


# To load Order page
@never_cache
def orders(request):
    if request.session.has_key('login'):
        uname = request.session['login']
        user = User.objects.get(username=uname)
        usr = Userprofile.objects.get(user=user)
        order = Order.objects.filter(user=usr).order_by('-date')
        c = Category.objects.all()
        if not order.exists():
            context = {
                'order': order,
                'err': 'Your haven\'t ordered',
                'cat': c,
                'user': uname
            }
            return render(request, 'landing/order.html', context)
        else:
            return render(request, 'landing/order.html', {'order': order, 'cat': c, 'user': uname})
    else:
        return redirect('/signin')

# To change the delivery status when user cancel or return
def order_stat(request):
    if request.method == 'GET':
        id = int(request.GET['oid'])
        order = Order.objects.get(id=id)
        pro = Product.objects.get(id=order.pro.id)
        pro.stock += order.qty
        pro.save()
        if order.status == 'Delivered':
            order.status = 'Returned'
        else:
            order.status = 'Cancelled'

        order.save()
        data = {
            'stat': order.status
        }
        return JsonResponse(data)

# To save the username in session during google signin
@never_cache
def social(request):
    username = request.user.username
    user = User.objects.get(username=username)
    auth.logout(request)
    request.session['login'] = username
    if not Userprofile.objects.filter(user=user).exists():
        usr = Userprofile.objects.create(
            user=user, uimage='userimage/user.png')
        usr.save()
    guest_to_user(request)
    return redirect('/')

# User profile loading function
@never_cache
def profile(request):
    if request.session.has_key('login'):
        uname = request.session['login']
        user = User.objects.get(username=uname)
        usr = Userprofile.objects.get(user=user)
        addr = Useraddr.objects.filter(user=usr)
        addr.filter(saddr=False).delete()
        context = {
            'user': usr,
            'addr': addr
        }
        return render(request, 'landing/userprofile.html', context)
    else:
        return redirect('/signin')

# Function to edit user profile
@never_cache
def edituser(request):
    if request.session.has_key('login'):
        f = 0
        uname = request.session['login']
        user = User.objects.get(username=uname)
        usr = Userprofile.objects.get(user=user)
        form = Userprofilef(request.POST or None,
                            request.FILES or None, instance=usr)
        if request.method == 'POST':
            num = request.POST['num']
            uname = request.POST['uname']
            lname = request.POST['lname']
            fname = request.POST['fname']
            email = request.POST['email']
            if Userprofile.objects.filter(number=num).exists() and usr.number != num:
                messages.info(request, "Phone number already exits")
                f = 1
            if User.objects.filter(username=uname).exists() and user.username != uname:
                messages.info(request, "Username already exits")
                f = 1
            if User.objects.filter(email=email).exists() and user.email != email:
                messages.info(request, "Email Id already exits")
                f = 1
            if f == 1:
                context = {
                    'form': form,
                    'user': usr
                }
                return render(request, 'landing/edituser.html', context)
            else:
                user.first_name = fname
                user.last_name = lname
                user.email = email
                user.username = uname
                user.save()
                usr.number = num
                if form.is_valid():
                    form.save()
                usr.save()
                return redirect('/profile')
        else:
            context = {
                'form': form,
                'user': usr
            }
            return render(request, 'landing/edituser.html', context)
    else:
        return redirect('/signin')

# Function to change user password
@never_cache
def change_pass(request):
    if request.session.has_key('login'):
        uname = request.session['login']
        user = User.objects.get(username=uname)
        usr = Userprofile.objects.get(user=user)
        if request.method == 'POST':
            cpass = request.POST['cpass']
            npass = request.POST['npass']
            cnpass = request.POST['cnpass']
            cuser = auth.authenticate(username=uname, password=cpass)
            if cuser:
                if npass == cnpass:
                    cuser.password = npass
                    cuser.save()
                    return redirect('/profile')
                else:
                    return render(request, 'landing/userprofile.html', {'err': 'Password Mismatch', 'user': usr})
            else:
                return render(request, 'landing/userprofile.html', {'err': 'Wrong Password', 'user': usr})
    else:
        return redirect('/signin')

# Function to delete user saved address
@never_cache
def deladdr(request, id):
    addr = Useraddr.objects.get(id=id)
    addr.delete()
    return redirect('/profile')

# Function on applying coupon
def coupon_apply(request):
    f = 2
    if request.method == 'GET':
        code = request.GET['code']
        uname = request.session['login']
        user = User.objects.get(username=uname)
        usr = Userprofile.objects.get(user=user)
        if request.session.has_key('buy_now'):
            pro=Product.objects.get(id=request.session['buy_now'])
            tot=pro.finalprice
        else:
            total=Cart.objects.filter(user=usr).aggregate(Sum('sub_tot'))
            tot=total['sub_tot__sum']
        if Coupon.objects.filter(coupon_code=code).exists():
            coupon = Coupon.objects.get(coupon_code=code)
            if Order.objects.filter(user=usr, coupon=coupon):
                return JsonResponse({'f': 1})
            else:
                tot -= (tot*coupon.offer/100)
                request.session['coupon'] = coupon.id
                context = {
                    'tot': tot,
                    'f': f
                }
            return JsonResponse(context)
        else:
            return JsonResponse({'f': 0})

# For searching products
@never_cache
def search(request):
    if request.method == 'POST':
        if request.session.has_key('login'):
            user = request.session['login']
        else:
            user = None
        if request.session.has_key('buy_now'):
            del request.session['buy_now']
        search = request.POST['search']
        c = Category.objects.all()
        prolist = Product.objects.filter(
            pro_name__icontains=search).order_by('-date')
        context = {
            'pro': prolist,
            'user': user,
            'cat': c,
            'cname': None
        }
        return render(request, 'landing/product.html', context)
    else:
        return render('/')

# To select the product in a price range
def price_sort(request):
    if request.method=='POST':
        price=int(request.POST['price'])
        cnam=request.POST['cname']
        c = Category.objects.all()
        if cnam!='':
            cname=Category.objects.get(cat_name=cnam)
            if price==1:
                pro=Product.objects.filter(category=cname).order_by('-finalprice')
            else:
                pro=Product.objects.filter(category=cname).order_by('finalprice')
        else:
            if price==1:
                pro=Product.objects.all().order_by('-finalprice')
            else:
                pro=Product.objects.all().order_by('finalprice')
        return render(request,'landing/product.html',{'pro':pro,'cat': c,'cname':cnam})

# Function for buy now
def buy_now(request,id):
    request.session['buy_now']=id
    return redirect('/setaddr')

# OTP resend
def otp_resend(request):
    print(request.session['num'])
    if send(request.session['num']):
        return render(request, 'landing/otp.html', {'url': '/otp'})
