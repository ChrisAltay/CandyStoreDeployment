from django.contrib.admin.views.decorators import staff_member_required
from .forms import CandyForm


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
