# Generated by Django 3.1.4 on 2021-04-16 16:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0041_thumbnail_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thumbnail',
            name='blob',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.blob'),
        ),
        migrations.AlterField(
            model_name='thumbnail',
            name='original',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.digest'),
        ),
    ]
