# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-15 22:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='featured',
            new_name='is_featured',
        ),
        migrations.RenameField(
            model_name='product',
            old_name='listed',
            new_name='is_listed',
        ),
        migrations.RenameField(
            model_name='product',
            old_name='useable',
            new_name='is_useable',
        ),
        migrations.AlterField(
            model_name='product',
            name='cost',
            field=models.DecimalField(decimal_places=0, default=10, max_digits=10),
        ),
        migrations.AlterField(
            model_name='product',
            name='discount_cost',
            field=models.DecimalField(blank=True, decimal_places=0, max_digits=8, null=True),
        ),
    ]