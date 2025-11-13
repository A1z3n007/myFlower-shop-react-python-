from django.core.management.base import BaseCommand
from shop.models import Product

DATA = [
    # 20 товаров (иконки/фото — Unsplash, категории разные)
    {"name":"Букет «Нежность»","category":"розы","price":12000,"image_url":"https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=800&q=80","desc":"Нежные розы пастельных оттенков."},
    {"name":"Тюльпаны микс","category":"тюльпаны","price":9000,"image_url":"https://images.unsplash.com/photo-1520280398531-0478a46fbb4b?w=800&q=80","desc":"Весенний микс ярких тюльпанов."},
    {"name":"Ромашковое поле","category":"ромашки","price":7000,"image_url":"https://images.unsplash.com/photo-1493666438817-866a91353ca9?w=800&q=80","desc":"Лёгкая композиция из ромашек."},
    {"name":"Пионы королевские","category":"пионы","price":18000,"image_url":"https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=800&q=80","desc":"Пышные пионы — королевы букетов."},
    {"name":"Лилии белые","category":"лилии","price":14000,"image_url":"https://images.unsplash.com/photo-1496062031456-07b8f162a322?w=800&q=80","desc":"Изысканные белые лилии."},
    {"name":"Розы красные 25 шт.","category":"розы","price":22000,"image_url":"https://images.unsplash.com/photo-1519681393784-d120267933ba?w=800&q=80","desc":"Классический букет из 25 роз."},
    {"name":"Эустома с зеленью","category":"эустома","price":15000,"image_url":"https://images.unsplash.com/photo-1498575207490-3e4c519225b7?w=800&q=80","desc":"Нежная эустома с эвкалиптом."},
    {"name":"Сирень ароматная","category":"сирень","price":11000,"image_url":"https://images.unsplash.com/photo-1528493366314-e317cd98dd12?w=800&q=80","desc":"Весенняя сирень."},
    {"name":"Подсолнухи мини","category":"подсолнухи","price":8000,"image_url":"https://images.unsplash.com/photo-1501004318641-b39e6451bec6?w=800&q=80","desc":"Яркие подсолнухи мини."},
    {"name":"Ирисы голубые","category":"ирисы","price":10000,"image_url":"https://images.unsplash.com/photo-1520975954732-35dd229bb2a6?w=800&q=80","desc":"Стильные ирисы."},
    {"name":"Герберы микс","category":"герберы","price":9500,"image_url":"https://images.unsplash.com/photo-1519681393786-7e4e3a3c6b24?w=800&q=80","desc":"Разноцветные герберы."},
    {"name":"Орхидеи фаленопсис","category":"орхидеи","price":26000,"image_url":"https://images.unsplash.com/photo-1524594227084-34c1c1a6b1b5?w=800&q=80","desc":"Элегантные орхидеи."},
    {"name":"Альстромерии пастель","category":"альстромерии","price":8500,"image_url":"https://images.unsplash.com/photo-1508057198894-247b23fe5ade?w=800&q=80","desc":"Нежные альстромерии."},
    {"name":"Хризантемы белые","category":"хризантемы","price":7800,"image_url":"https://images.unsplash.com/photo-1457089328109-e5d9bd499191?w=800&q=80","desc":"Классические хризантемы."},
    {"name":"Суккуленты микс","category":"суккуленты","price":6000,"image_url":"https://images.unsplash.com/photo-1463320898484-cdee8141c787?w=800&q=80","desc":"Неприхотливый микс."},
    {"name":"Лаванда сухоцвет","category":"лаванда","price":5000,"image_url":"https://images.unsplash.com/photo-1464983953574-0892a716854b?w=800&q=80","desc":"Ароматная лаванда."},
    {"name":"Каллы белые","category":"каллы","price":17000,"image_url":"https://images.unsplash.com/photo-1464961968964-a9e0b1b8a8a1?w=800&q=80","desc":"Стильные каллы."},
    {"name":"Микс полевых","category":"полевые","price":9000,"image_url":"https://images.unsplash.com/photo-1486649567693-aaa9b2e5932c?w=800&q=80","desc":"Свежий полевой букет."},
    {"name":"Гортензии голубые","category":"гортензии","price":20000,"image_url":"https://images.unsplash.com/photo-1479936343636-73cdc5aae0c3?w=800&q=80","desc":"Объёмные гортензии."},
    {"name":"Авторский букет","category":"эксклюзив","price":30000,"image_url":"https://images.unsplash.com/photo-1501004318641-b39e6451bec6?w=800&q=80","desc":"Собран под заказ."},
]

class Command(BaseCommand):
    help = "Seed 20 demo products"

    def handle(self, *args, **options):
        created = 0
        for d in DATA:
            obj, was_created = Product.objects.get_or_create(
                name=d["name"],
                defaults=d
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded products: {created}"))
