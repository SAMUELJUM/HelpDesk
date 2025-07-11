# Generated by Django 5.2.1 on 2025-06-15 05:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helpdes', '0003_category_department'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='department',
            name='name',
            field=models.CharField(max_length=255),
        ),
    ]
