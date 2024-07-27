import secrets

from django.db import models


class TelegramUser(models.Model):
    user_id = models.IntegerField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_super_admin = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_courier = models.BooleanField(default=False)
    referred_by = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    balance = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.username if self.username else "None"


class Rule(models.Model):
    bot_rule = models.TextField()


class Review(models.Model):
    RATING = ((1, "1"),
              (2, "2"),
              (3, "3"),
              (4, "4"),
              (5, "5"))
    user = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField(choices=RATING)
    text = models.TextField()


class Gram(models.Model):
    chapter = models.ForeignKey("Chapter", on_delete=models.CASCADE)
    gram = models.FloatField()
    usd = models.IntegerField()


class Product(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='user')
    courier = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='courier')
    gram = models.ForeignKey(Gram, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    sold = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)




class Promo(models.Model):
    promo_text = models.CharField(max_length=5, unique=True)
    amount = models.PositiveIntegerField()
    used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.promo_text = secrets.token_urlsafe(5)
        while Promo.objects.filter(promo_text=self.promo_text).exists():
            self.promo_text = secrets.token_urlsafe(5)
        super().save(*args, **kwargs)


class Chapter(models.Model):
    title = models.CharField(max_length=255, unique=True)
    photo = models.CharField(max_length=555, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    pervomaysky = models.ManyToManyField(Product, related_name='pervomaysky', blank=True)
    oktyabrsky = models.ManyToManyField(Product, related_name='oktyabrsky', blank=True)
    leninsky = models.ManyToManyField(Product, related_name='leninsky', blank=True)
    sverdlovsky = models.ManyToManyField(Product, related_name='sverdlovsky', blank=True)

    def __str__(self):
        return self.title


class ChannelToAnnounce(models.Model):
    text = models.TextField()


class LostUserProduct(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True)
    lost_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    added_to_balance = models.PositiveIntegerField()

