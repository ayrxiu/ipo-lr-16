from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Maker, Cart, CartItem, Order
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO
import xlsxwriter
from django.http import HttpResponse
from datetime import datetime
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .permissions import IsAdminOrReadOnly
from rest_framework import viewsets, permissions
from .serializers import (
    ProductSerializer, CategorySerializer, MakerSerializer,
    CartSerializer, CartItemSerializer
)


# ==================== РЕГИСТРАЦИЯ ====================
class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')


# ==================== ГЛАВНАЯ СТРАНИЦА ====================
def home(request):
    popular_products = Product.objects.all().order_by('-id')[:6]
    categories = Category.objects.all()
    context = {
        'popular_products': popular_products,
        'categories': categories,
    }
    return render(request, 'shop/index.html', context)


# ==================== КАТАЛОГ С ФИЛЬТРАМИ ====================
def catalog_view(request):
    category_id = request.GET.get('category')
    maker_id = request.GET.get('maker')
    search_query = request.GET.get('search', '')

    products = Product.objects.all()

    if category_id:
        products = products.filter(category_id=category_id)
    if maker_id:
        products = products.filter(maker_id=maker_id)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(definition__icontains=search_query)
        )

    categories = Category.objects.all()
    makers = Maker.objects.all()

    context = {
        'products': products,           # 👈 ДОБАВЬТЕ ЭТУ СТРОКУ!
        'categories': categories,
        'makers': makers,
        'selected_category': category_id,
        'selected_maker': maker_id,
        'search_query': search_query,
    }
    return render(request, 'shop/catalog.html', context)

# ==================== СТАРЫЙ product_list (МОЖНО УДАЛИТЬ, НО ОСТАВИМ) ====================
def product_list(request):
    products = Product.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(definition__icontains=search_query)
        )
    
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    maker_id = request.GET.get('maker')
    if maker_id:
        products = products.filter(maker_id=maker_id)
    
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'quantity':
        products = products.order_by('-quantity')
    
    categories = Category.objects.all()
    makers = Maker.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'makers': makers,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_maker': maker_id,
        'selected_sort': sort_by,
    }
    return render(request, 'shop/product_list.html', context)


# ==================== ДЕТАЛЬНАЯ СТРАНИЦА ТОВАРА ====================
def product_detail(request, pk):
    product = get_object_or_404(Product, id=pk)
    return render(request, 'shop/product_detail.html', {'product': product})


# ==================== КОРЗИНА ====================
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        if cart_item.quantity < product.quantity:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f'Товар "{product.name}" добавлен в корзину!')
        else:
            messages.error(request, f'Недостаточно товара на складе. Доступно: {product.quantity} шт.')
    else:
        messages.success(request, f'Товар "{product.name}" добавлен в корзину!')
    
    # После добавления возвращаем пользователя на ту страницу, откуда он нажал кнопку
    return redirect(request.META.get('HTTP_REFERER', 'catalog'))

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        new_quantity = int(request.POST.get('quantity', 1))
        
        if new_quantity <= 0:
            cart_item.delete()
            return redirect('view_cart')
        
        if new_quantity <= cart_item.product.quantity:
            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            messages.error(request, f'Недостаточно товара на складе. Доступно: {cart_item.product.quantity} шт.')
    
    return redirect('view_cart')


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        cart_item.delete()
    
    return redirect('view_cart')


@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'shop/cart.html', {'cart': cart})


# ==================== ОФОРМЛЕНИЕ ЗАКАЗА ====================
@login_required
def checkout(request):
    cart = Cart.objects.get(user=request.user)
    
    if request.method == 'POST':
        address = request.POST.get('address', '')
        
        if not address:
            messages.error(request, 'Пожалуйста, укажите адрес доставки')
            return render(request, 'shop/checkout.html', {'cart': cart})
        
        if cart.items.count() == 0:
            messages.error(request, 'Корзина пуста')
            return redirect('view_cart')
        
        order = Order.objects.create(
            user=request.user,
            address=address,
            total_price=cart.total_price()
        )
        
        excel_file = generate_invoice_excel(order, cart)
        send_invoice_email(request.user.email, excel_file, order)
        
        cart.items.all().delete()
        
        messages.success(request, f'Заказ #{order.id} оформлен! Чек отправлен на вашу почту.')
        return redirect('view_cart')
    
    return render(request, 'shop/checkout.html', {'cart': cart})


def generate_invoice_excel(order, cart):
    """Генерация Excel файла с чеком"""
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Чек')
    
    title_format = workbook.add_format({'bold': True, 'size': 16, 'align': 'center'})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2'})
    money_format = workbook.add_format({'num_format': '#,##0.00'})
    
    worksheet.merge_range('A1:D1', f'ЧЕК #{order.id}', title_format)
    
    worksheet.write('A3', 'Дата:')
    worksheet.write('B3', order.created_at.strftime('%d.%m.%Y %H:%M'))
    worksheet.write('A4', 'Покупатель:')
    worksheet.write('B4', order.user.username)
    worksheet.write('A5', 'Адрес доставки:')
    worksheet.write('B5', order.address)
    
    row = 7
    worksheet.write(row, 0, 'Товар', header_format)
    worksheet.write(row, 1, 'Кол-во', header_format)
    worksheet.write(row, 2, 'Цена', header_format)
    worksheet.write(row, 3, 'Сумма', header_format)
    
    row += 1
    for item in cart.items.all():
        worksheet.write(row, 0, item.product.name)
        worksheet.write(row, 1, item.quantity)
        worksheet.write(row, 2, float(item.product.price), money_format)
        worksheet.write(row, 3, float(item.total_price()), money_format)
        row += 1
    
    row += 1
    worksheet.write(row, 2, 'ИТОГО:', header_format)
    worksheet.write(row, 3, float(order.total_price), money_format)
    
    worksheet.set_column('A:A', 30)
    worksheet.set_column('B:B', 10)
    worksheet.set_column('C:C', 15)
    worksheet.set_column('D:D', 15)
    
    workbook.close()
    output.seek(0)
    
    # Сохраняем Excel файл на диск для проверки
    with open(f'invoice_{order.id}.xlsx', 'wb') as f:
        f.write(output.getvalue())
    print(f"✅ Excel файл сохранен: invoice_{order.id}.xlsx")
    
    return output


def send_invoice_email(email, excel_file, order):
    """Отправка чека по email"""
    subject = f'Чек на заказ #{order.id}'
    message = f"""
    Здравствуйте!
    
    Ваш заказ #{order.id} успешно оформлен.
    Сумма заказа: {order.total_price} руб.
    Адрес доставки: {order.address}
    
    Чек прикреплен к письму.
    
    Спасибо за покупку!
    """
    
    print("=" * 50)
    print("📧 ОТПРАВКА ПИСЬМА:")
    print(f"To: {email}")
    print(f"Subject: {subject}")
    print(f"Message: {message}")
    print("=" * 50)
    
    email_message = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )
    
    email_message.attach('invoice.xlsx', excel_file.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    email_message.send()
    
    print("✅ ПИСЬМО ОТПРАВЛЕНО!")
    print("=" * 50)


# ==================== API VIEWS (DRF) ====================
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]   


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class MakerViewSet(viewsets.ModelViewSet):
    queryset = Maker.objects.all()
    serializer_class = MakerSerializer
    permission_classes = [permissions.IsAuthenticated]


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin
from .models import Profile, Order
from .serializers import ProfileSerializer, OrderSerializer

# API: получение и обновление профиля текущего пользователя
class ProfileView(RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return Profile.objects.get(user=self.request.user)

# API: список заказов текущего пользователя (или всех для админа)
class OrderListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or (hasattr(user, 'profile') and user.profile.role == 'admin'):
            return Order.objects.all().order_by('-created_at')
        return Order.objects.filter(user=user).order_by('-created_at')

# Страница личного кабинета (шаблон)
def profile_page(request):
    return render(request, 'shop/profile.html')