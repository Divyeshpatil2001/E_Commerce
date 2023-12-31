from django.shortcuts import render,redirect
from django.http import HttpResponse
from app1.models import *
# Create your views here.

def data(request):
    return HttpResponse("<h1>This is my first webpage</h1>")


def index(request):
    a=Category.objects.all()

    return render(request,"index.html",{'data':a})

def productall(request):
    a=Product.objects.all()
    return render(request,"product.html",{'data':a})

def productfilter(request,id):
    a=Product.objects.filter(Category=id)
    return render(request,"product.html",{'data':a})

def productget(request,id):
    a=Product.objects.get(id=id)
    return render(request,'product_details.html',{'data':a})


def register(request):
    if request.method=="POST":
        name1=request.POST['name']
        email1=request.POST['email']
        number1=request.POST['number']
        address1=request.POST['address']
        password1=request.POST['password']
        user=Userregister(name=name1,email=email1,number=number1,address=address1,password=password1)
        data=Userregister.objects.filter(email=email1)
        if  len(data)==0:
            user.save()
            return redirect('login')
        else:
            return render(request,"register.html",{'m':'user alredy exist'})
    return render(request,"register.html")

def login(request):
    if request.method=="POST":
        email1=request.POST['email']
        password1=request.POST['password']
        try:
            user=Userregister.objects.get(email=email1,password=password1)
            if user:
                request.session['email']=user.email
                request.session['id']=user.pk
                return redirect('index1')
            else:
                return render(request,"login.html",{'m':'invalid data enter'})
        except:
            return render(request,"login.html",{'m':'invalid data enter'})
    return render(request,"login.html")

def logout(request):
    if 'email' in request.session:
        del request.session['email']
        del request.session['id']
        return redirect('login')
    else:
        return redirect('login')
    

def profile(request):
    if 'email' in request.session:
        user=Userregister.objects.get(email=request.session['email'])
        if request.method=="POST":
            name1=request.POST['name']
            number1=request.POST['number']
            address1=request.POST['address']
            oldpasss=request.POST['oldpassword']
            newpass=request.POST['newpassword']
            user.name=name1
            user.number=number1
            user.address=address1 
            if oldpasss=="" and newpass=="":
                user.save()
                return render(request,'profile.html',{'user':user,'m':'Profile Updated..'})
            if user.password==oldpasss:
                user.password=newpass
                user.save()
                return render(request,'profile.html',{'user':user,'m':'Profile Updated..'})
            else:
                return render(request,'profile.html',{'user':user,'m':'invalid old password..'})
        return render(request,'profile.html',{'user':user})
    else:
        return redirect('login')



def ordertable(request):
    if 'email' in request.session:
        orderdata=Order.objects.filter(userid=request.session['id'])
        productlist=[]
        for i in orderdata:
            productdict={}
            productdata=Product.objects.get(id=i.productid)
            productdict['image']=productdata.image
            productdict['name']=productdata.name
            productdict['quantity']=i.quantity
            productdict['price']=i.price
            productdict['date']=i.datetime
            productdict['transactionid']=i.transactionid
            productlist.append(productdict)
        return render(request,'ordertable.html',{'productlist':productlist})
    else:
        return redirect('login')

def ordersucess(request):
    if 'email' in request.session:
        return render(request,'order_sucess.html')
    else:
        return redirect('login')









import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest

def buynow(request):
    if 'email' in request.session:
        if request.method=="POST":
            request.session['productid']=request.POST['productid']
            productdata=Product.objects.get(id=request.POST['productid'])
            request.session['quantity']="1"
            request.session['price']=str(int(request.session['quantity'])*productdata.price)
            request.session['paymentmethod']="Razorpay"
            return redirect('razorpayView')  
    else:
        return redirect('login')





RAZOR_KEY_ID = 'rzp_test_inZsW59bi3pjxv'
RAZOR_KEY_SECRET = 'VnlgFFlD1apHIobsVdPsiLnC'
client = razorpay.Client(auth=(RAZOR_KEY_ID, RAZOR_KEY_SECRET))

def razorpayView(request):
    currency = 'INR'
    amount = int(request.session['price'])*100
    # Create a Razorpay Order
    razorpay_order = client.order.create(dict(amount=amount,currency=currency,payment_capture='0'))
    # order id of newly created order.
    razorpay_order_id = razorpay_order['id']
    callback_url = 'http://127.0.0.1:8000/paymenthandler/'    
    # we need to pass these details to frontend.
    context = {}
    context['razorpay_order_id'] = razorpay_order_id
    context['razorpay_merchant_key'] = RAZOR_KEY_ID
    context['razorpay_amount'] = amount
    context['currency'] = currency
    context['callback_url'] = callback_url    
    return render(request,'razorpayDemo.html',context=context)

@csrf_exempt
def paymenthandler(request):
    # only accept POST request.
    if request.method == "POST":
        try:
            # get the required parameters from post request.
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
 
            # verify the payment signature.
            result = client.utility.verify_payment_signature(
                params_dict)
            
            amount = int(request.session['price'])*100  # Rs. 200
            # capture the payemt
            client.payment.capture(payment_id, amount)

            #Order Save Code
            orderModel = Order()
            orderModel.userid=request.session['id']
            orderModel.productid=request.session['productid']
            orderModel.quantity=request.session['quantity']
            orderModel.price = request.session['price']
            orderModel.paymentMethod = request.session['paymentmethod']
            orderModel.transactionid = payment_id
            productdata=Product.objects.get(id=request.session['productid'])
            productdata.quantity=productdata.quantity-int(request.session['quantity'])
            productdata.save()
            orderModel.save()
            del request.session['productid']
            del request.session['quantity']
            del request.session['price']
            del request.session['paymentmethod']
            # render success page on successful caputre of payment
            return redirect('orderSuccessView')
        except:
            print("Hello")
            # if we don't find the required parameters in POST data
            return HttpResponseBadRequest()
    else:
        print("Hello1")
       # if other than POST request is made.
        return HttpResponseBadRequest()

