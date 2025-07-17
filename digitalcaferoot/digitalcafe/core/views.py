from django.http import HttpResponse
from django.template import loader
from .models import CartItem, Product #added cartitem model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
import datetime as dt
from .models import Transaction
from .models import LineItem



@login_required
def index(request):
    template = loader.get_template("core/index.html")
    products = Product.objects.all()
    context = {
        "user": request.user,
        "product_data": products,
    }
    return HttpResponse(template.render(context, request))



@login_required
def product_detail(request, product_id):
    # if the user is just viewing the page (GET request)
    if request.method == 'GET': 
        template = loader.get_template("core/product_detail.html") # load the HTML file
        p = Product.objects.get(id=product_id) # get the product from Product model database
        context = {
            "product": p # send that product into the HTML template
        }
        return HttpResponse(template.render(context, request)) # render HTML with product data
    
    # if the user submits the "Add to cart" form (POST request)
    elif request.method == 'POST': 
        submitted_quantity = request.POST['quantity'] # get quantity from the form
        submitted_product_id = request.POST['product_id'] # get product_id from the form
        product = Product.objects.get(id=submitted_product_id) # get product from Product model database
        user = request.user # gives you the currently logged-in user

        # tell Django to save user, product and quantity into the CartItem model database
        cart_item = CartItem(user=user, product=product, quantity=submitted_quantity)  
        cart_item.save() 
        
        # display the message
        messages.add_message(
            request,
            messages.INFO,
            f'Added {submitted_quantity} of {product.name} to your cart'
        )
        return redirect('index') # after saving bring the user back to the homepage



def login_view(request):
    # if user is just visiting the page (GET), show the login form
    if request.method == 'GET':
        template = loader.get_template("core/login_view.html")
        context = {}
        return HttpResponse(template.render(context, request))
    
    # if user submits a form (POST), check their username and pass
    # if it matches, it returns a 'user_object'; if not, then it returns 'none'
    elif request.method == 'POST':
        submitted_username = request.POST['username']
        submitted_password = request.POST['password']
        user_object = authenticate(
            username=submitted_username,
            password=submitted_password
        )
        if user_object is None: 
            messages.add_message(request, messages.INFO, 'Invalid login.')
            return redirect(request.path_info)
        login(request, user_object)
        return redirect('index')
    


@login_required
def checkout(request):
    if request.method == 'GET':
        template = loader.get_template("core/checkout.html")
        cart_items = CartItem.objects.filter(user=request.user)
        context = {
            'cart_items': list(cart_items),
        }
        return HttpResponse(template.render(context, request))
    
    # if the user clicks 'Checkout' in /checkout
    elif request.method == 'POST':
        cart_items = CartItem.objects.filter(user=request.user) # gets the user’s current cart
        # Create new transaction
        created_at = dt.datetime.now(tz=dt.timezone.utc)
        transaction = Transaction(user=request.user, created_at=created_at)
        transaction.save()
        
        
        for cart_item in cart_items:
            # create a line_item for each cart_item (based on the product and qty fr the Trasaction model)
            line_item = LineItem(
                transaction=transaction,
                product=cart_item.product,
                quantity=cart_item.quantity,
            )
            line_item.save()
            cart_item.delete()
        
        # adds a temporary message to display when the user lands back on the homepage
        messages.add_message(request, messages.INFO, f'Thank you for your purchase!')
        return redirect('index')



@login_required
def transaction_history(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    line_items_by_transaction = {}

    for transaction in transactions:
        line_items = LineItem.objects.filter(transaction=transaction)
        line_items_by_transaction[transaction.id] = line_items

    template = loader.get_template("core/transaction_history.html")
    context = {
        'transactions': transactions,
        'line_items_by_transaction': line_items_by_transaction,
    }
    return HttpResponse(template.render(context, request))