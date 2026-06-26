from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Maker(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    definition = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    definition = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# ИСПРАВЛЕННАЯ МОДЕЛЬ С КАРТИНКАМИ-ССЫЛКАМИ
class Product(models.Model):
    name = models.CharField(max_length=200)
    definition = models.TextField()
    # Изменили ImageField на CharField, чтобы хранить URL-ссылки из интернета
    photo = models.CharField(max_length=500, blank=True, null=True, verbose_name="Ссылка на фото")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    maker = models.ForeignKey(Maker, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def clean(self):
        if self.price < 0:
            raise ValidationError('Цена не может быть отрицательной')
        if self.quantity < 0:
            raise ValidationError('Количество не может быть отрицательным')

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"

    def total_price(self):
        total = 0
        for item in self.items.all():
            total += item.total_price()
        return total

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} ({self.quantity} шт.)"

    def total_price(self):
        return self.product.price * self.quantity

    def clean(self):
        if self.quantity > self.product.quantity:
            raise ValidationError('Количество не может превышать остаток на складе')
    
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.TextField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Заказ #{self.id} - {self.user.username}"


from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    ROLE_CHOICES = (
        ('customer', 'Покупатель'),
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    favorite_category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()