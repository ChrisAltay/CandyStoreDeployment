"""
Store views for browsing candies
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from .models import Candy, Order, OrderItem
from .cart import Cart


from django.contrib.admin.views.decorators import staff_member_required
from .forms import CandyForm, CheckoutForm


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


from django.contrib import messages


@require_POST
@login_required(login_url="login")
def order_create(request):
    cart = Cart(request)
    if len(cart) > 0:
        if request.user.is_authenticated:
            user = request.user
        else:
            user = None

        # Verify stock first
        for item in cart:
            if item["product"].stock < item["quantity"]:
                messages.error(
                    request,
                    f"Not enough stock for {item['product'].name}. Only {item['product'].stock} left.",
                )
                return redirect("cart_detail")

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


@login_required(login_url="login")
def order_status_api(request, order_id):
    """API endpoint for live order status updates"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Trigger simulation update
    order.update_status_based_on_time()

    data = {
        "status": order.status,
        "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        "is_shipped": order.status in [Order.STATUS_SHIPPED, Order.STATUS_DELIVERED],
        "is_delivered": order.status == Order.STATUS_DELIVERED,
    }
    return JsonResponse(data)


@staff_member_required
def inventory_list(request):
    """List all products for inventory management"""
    candies = Candy.objects.all()
    return render(request, "store/inventory_list.html", {"candies": candies})


@staff_member_required
def inventory_add(request):
    """Add a new product"""
    if request.method == "POST":
        form = CandyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("inventory_list")
    else:
        form = CandyForm()

    return render(
        request, "store/inventory_form.html", {"form": form, "title": "Add Product"}
    )


@staff_member_required
def inventory_update(request, pk):
    """Update an existing product"""
    candy = get_object_or_404(Candy, pk=pk)
    if request.method == "POST":
        form = CandyForm(request.POST, instance=candy)
        if form.is_valid():
            form.save()
            return redirect("inventory_list")
    else:
        form = CandyForm(instance=candy)

    return render(
        request, "store/inventory_form.html", {"form": form, "title": "Update Product"}
    )


@login_required(login_url="login")
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect("cart_detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Verify stock availability first
            for item in cart:
                if item["product"].stock < item["quantity"]:
                    messages.error(
                        request,
                        f"Not enough stock for {item['product'].name}. Only {item['product'].stock} left.",
                    )
                    return redirect("cart_detail")

            # Process mock payment
            order = Order.objects.create(
                user=request.user,
                total_price=cart.get_total_price(),
                full_name=form.cleaned_data["full_name"],
                address=form.cleaned_data["address"],
                city=form.cleaned_data["city"],
                zip_code=form.cleaned_data["zip_code"],
            )
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                )
                # Deduct stock
                product = item["product"]
                product.stock -= item["quantity"]
                product.save()

            cart.clear()
            return render(request, "store/order_created.html", {"order": order})
    else:
        form = CheckoutForm()

    return render(request, "store/checkout.html", {"cart": cart, "form": form})


@require_POST
@login_required(login_url="login")
def cancel_order(request, order_id):
    """Cancel an order and restore stock"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.cancel_order():
        messages.success(
            request,
            f"Order #{order.id} has been cancelled successfully. Stock has been restored.",
        )
    else:
        messages.error(
            request,
            f"Order #{order.id} cannot be cancelled. Only orders with 'Created' status can be cancelled.",
        )

    return redirect("order_detail", order_id=order.id)


@login_required(login_url="login")
def reorder(request, order_id):
    """Copy all items from a previous order to the cart"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    cart = Cart(request)

    added_items = []
    out_of_stock_items = []

    for item in order.items.all():
        if item.product.stock >= item.quantity:
            cart.add(
                product=item.product, quantity=item.quantity, override_quantity=False
            )
            added_items.append(item.product.name)
        else:
            out_of_stock_items.append(
                f"{item.product.name} (only {item.product.stock} available)"
            )

    if added_items:
        messages.success(request, f"Added to cart: {', '.join(added_items)}")

    if out_of_stock_items:
        messages.warning(
            request,
            f"Out of stock or insufficient quantity: {', '.join(out_of_stock_items)}",
        )

    return redirect("cart_detail")


from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO


@login_required(login_url="login")
def download_invoice(request, order_id):
    """Generate and download PDF invoice for an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#4f46e5"),
        spaceAfter=30,
        alignment=TA_CENTER,
    )

    # Title
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Spacer(1, 12))

    # Order Information
    order_info = [
        ["Order Number:", f"#{order.id}"],
        ["Order Date:", order.created_at.strftime("%B %d, %Y at %I:%M %p")],
        ["Status:", order.status],
        ["Customer:", order.full_name or request.user.username],
    ]

    if order.address:
        order_info.append(
            ["Shipping Address:", f"{order.address}, {order.city} {order.zip_code}"]
        )

    info_table = Table(order_info, colWidths=[2 * inch, 4 * inch])
    info_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # Items Table
    items_data = [["Item", "Quantity", "Unit Price", "Total"]]
    for item in order.items.all():
        items_data.append(
            [
                item.product.name,
                str(item.quantity),
                f"${item.price}",
                f"${item.price * item.quantity:.2f}",
            ]
        )

    # Add total row
    items_data.append(["", "", "Total:", f"${order.total_price}"])

    items_table = Table(
        items_data, colWidths=[3 * inch, 1 * inch, 1.2 * inch, 1.2 * inch]
    )
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -2), colors.beige),
                ("GRID", (0, 0), (-1, -2), 1, colors.black),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, -1), (-1, -1), 12),
                ("LINEABOVE", (2, -1), (-1, -1), 2, colors.black),
            ]
        )
    )
    elements.append(items_table)

    # Build PDF
    doc.build(elements)

    # Get PDF from buffer
    pdf = buffer.getvalue()
    buffer.close()

    # Create response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="invoice_order_{order.id}.pdf"'
    )
    response.write(pdf)

    return response


from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def add_to_watchlist(request, candy_id):
    """Add a product to user's watchlist"""
    from .models import ProductWatchlist

    if request.method == "POST":
        candy = get_object_or_404(Candy, id=candy_id)

        # Check if already in watchlist
        watchlist_item, created = ProductWatchlist.objects.get_or_create(
            user=request.user, product=candy, defaults={"auto_added": False}
        )

        if created:
            messages.success(request, f"Added {candy.name} to your watchlist!")
        else:
            messages.info(request, f"{candy.name} is already in your watchlist.")

    return redirect("candy_detail", candy_id=candy_id)
