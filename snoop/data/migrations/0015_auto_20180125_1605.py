# Generated by Django 2.0 on 2018-01-25 16:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0014_file_blob'),
    ]

    operations = [
        migrations.AlterField(
            model_name='directory',
            name='container_file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING,
                                    related_name='child_directory_set', to='data.File'),
        ),
        migrations.AlterField(
            model_name='directory',
            name='parent_directory',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING,
                                    related_name='child_directory_set', to='data.Directory'),
        ),
        migrations.AlterField(
            model_name='file',
            name='blob',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, to='data.Blob'),
        ),
        migrations.AlterField(
            model_name='task',
            name='blob_arg',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='data.Blob'),
        ),
        migrations.AlterField(
            model_name='task',
            name='date_finished',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='date_started',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='result',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, to='data.Blob'),
        ),
    ]
