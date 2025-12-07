"""
Store views for browsing candies
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import Candy, Order, OrderItem
from .cart import Cart


def home(request):
    """Home page showing all candies"""
    candies = Candy.objects.all()
    context = {
        "candies": candies,
    }
    return render(request, "store/home.html", context)


def candy_detail(request, candy_id):
    """Detail page for a single candy"""
    candy = get_object_or_404(Candy, id=candy_id)
    context = {
        "candy": candy,
    }
    return render(request, "store/candy_detail.html", context)


@require_POST
def cart_add(request, candy_id):
    cart = Cart(request)
    candy = get_object_or_404(Candy, id=candy_id)
    quantity = int(request.POST.get("quantity", 1))
    override = request.POST.get("override", False)
    cart.add(product=candy, quantity=quantity, override_quantity=override)
    return redirect("cart_detail")


@require_POST
def cart_remove(request, candy_id):
    cart = Cart(request)
    candy = get_object_or_404(Candy, id=candy_id)
    cart.remove(candy)
    return redirect("cart_detail")


def cart_detail(request):
    cart = Cart(request)
    return render(request, "store/cart.html", {"cart": cart})


from django.contrib.auth.decorators import login_required


@require_POST
@login_required(login_url="login")
def order_create(request):
    cart = Cart(request)
    if len(cart) > 0:
        if request.user.is_authenticated:
            user = request.user
        else:
            user = None

        order = Order.objects.create(user=user, total_price=cart.get_total_price())
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                price=item["price"],
                quantity=item["quantity"],
            )
            # Update stock
            product = item["product"]
            product.stock -= item["quantity"]
            product.save()
        cart.clear()
        return render(request, "store/order_created.html", {"order": order})
    return redirect("cart_detail")


@login_required(login_url="login")
def order_history(request):
    """List of orders for the current user"""
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    for order in orders:
        order.update_status_based_on_time()
    return render(request, "store/order_list.html", {"orders": orders})


@login_required(login_url="login")
def order_detail(request, order_id):
    """Order detail page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Simulate status updates
    order.update_status_based_on_time()

    return render(request, "store/order_detail.html", {"order": order})
