# Generated by Django 2.2.10 on 2021-03-28 15:51

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feh', '0020_remove_hero_icon_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='hero',
            name='harmonized_skill',
            field=models.CharField(blank=True, default=None, max_length=2000, null=True),
        ),
        migrations.AlterField(
            model_name='hero',
            name='availability',
            field=models.CharField(choices=[('A_STANDARD', 'Standard Pool'), ('A_SPECIAL', 'Special'), ('A_GHB', 'Grand Hero Battle'), ('A_TT', 'Tempest Trials'), ('A_LEGENDARY', 'Legendary'), ('A_MYTHIC', 'Mythic'), ('A_STORY', 'Story'), ('A_DUO', 'Duo'), ('A_HARMONIZED', 'Harmonized')], max_length=15),
        ),
        migrations.AlterField(
            model_name='skill',
            name='availabilities',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('A_STANDARD', 'Standard Pool'), ('A_SPECIAL', 'Special'), ('A_GHB', 'Grand Hero Battle'), ('A_TT', 'Tempest Trials'), ('A_LEGENDARY', 'Legendary'), ('A_MYTHIC', 'Mythic'), ('A_STORY', 'Story'), ('A_DUO', 'Duo'), ('A_HARMONIZED', 'Harmonized')], max_length=15), size=None),
        ),
    ]
