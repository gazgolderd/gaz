# Generated by Django 4.2.7 on 2024-07-27 10:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tg', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['created_at']},
        ),
    ]