
from .forms import CheckoutForm

@login_required(login_url="login")
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect("cart_detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Process mock payment (assumed successful if valid)
            order = Order.objects.create(
                user=request.user, total_price=cart.get_total_price()
            )
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                )
            cart.clear()
            # Redirect to order created/success page
            return render(request, "store/order_created.html", {"order": order})
    else:
        form = CheckoutForm()

    return render(request, "store/checkout.html", {"cart": cart, "form": form})
