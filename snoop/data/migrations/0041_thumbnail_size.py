# Generated by Django 3.1.4 on 2021-04-16 16:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0040_thumbnail'),
    ]

    operations = [
        migrations.AddField(
            model_name='thumbnail',
            name='size',
            field=models.IntegerField(choices=[(100, 'Small'), (200, 'Medium'), (400, 'Large')], default=200),
        ),
    ]
