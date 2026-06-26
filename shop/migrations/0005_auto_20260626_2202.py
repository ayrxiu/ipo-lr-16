from django.db import migrations

def fix_product_images(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    
    # Расширенный пул красивых картинок
    images_pool = {
        'spinning': 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?q=80&w=800&auto=format&fit=crop', # Удочки
        'reel': 'https://images.unsplash.com/photo-1611091531065-ef7e4360a89d?q=80&w=800&auto=format&fit=crop',     # Катушки
        'bait': 'https://cdn.pixabay.com/photo/2016/11/29/03/15/bait-1867011_1280.jpg',                             # Прикормки
        'lure': 'https://images.unsplash.com/photo-1516246838873-9d3265952d1b?q=80&w=800&auto=format&fit=crop',     # Блесны / Крючки
        'boat': 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=800&auto=format&fit=crop',     # Лодки / Экипировка
        'default': 'https://images.unsplash.com/photo-1517462964-21fdcec3f25b?q=80&w=800&auto=format&fit=crop'       # Общая рыбалка
    }

    for product in Product.objects.all():
        # Собираем в одну строку имя, описание и имя категории для точного поиска
        search_zone = f"{product.name} {product.definition or ''} {product.category.name if product.category else ''}".lower()
        
        if any(w in search_zone for w in ['удоч', 'спинн', 'удил', 'фидер', 'rod', 'pole']):
            product.photo = images_pool['spinning']
        elif any(w in search_zone for w in ['катуш', 'reel']):
            product.photo = images_pool['reel']
        elif any(w in search_zone for w in ['прикор', 'бойл', 'нажив', 'макух', 'bait']):
            product.photo = images_pool['bait']
        elif any(w in search_zone for w in ['блес', 'вобле', 'крюч', 'леск', 'поплав', 'приман', 'снаст', 'lure', 'hook']):
            product.photo = images_pool['lure']
        elif any(w in search_zone for w in ['лодк', 'эхолот', 'палат', 'костюм', 'сапог', 'ящик', 'boat']):
            product.photo = images_pool['boat']
        else:
            product.photo = images_pool['default']
            
        product.save()

def reverse_fix(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_auto_20260626_2150'),    ]

    operations = [
        migrations.RunPython(fix_product_images, reverse_code=reverse_fix),
    ]