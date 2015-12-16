# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-15 18:12
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import shop.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('listed', models.BooleanField(default=False)),
                ('useable', models.BooleanField(default=True)),
                ('featured', models.BooleanField(default=False)),
                ('title', models.CharField(max_length=120, null=True)),
                ('slug', models.SlugField(blank=True, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to=shop.models.upload_location)),
                ('description', models.TextField(blank=True, max_length=500, null=True)),
                ('cost', models.DecimalField(decimal_places=0, default=10, max_digits=12)),
                ('discount_cost', models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True)),
                ('max_downloads', models.PositiveIntegerField(blank=True, null=True)),
                ('promo_code', models.CharField(max_length=30)),
                ('list_date_start', models.DateTimeField(null=True, verbose_name='Listing Start Date')),
                ('list_date_end', models.DateTimeField(null=True, verbose_name='Listing Expiration')),
                ('use_date_start', models.DateTimeField(null=True, verbose_name='Usage Start Date')),
                ('use_date_end', models.DateTimeField(null=True, verbose_name='Usage Expiration')),
                ('buyers', models.ManyToManyField(blank=True, related_name='buyers', to=settings.AUTH_USER_MODEL)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('list_date_end',),
            },
        ),
    ]