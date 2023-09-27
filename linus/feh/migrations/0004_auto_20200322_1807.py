# Generated by Django 2.2.10 on 2020-03-22 18:07

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("feh", "0003_auto_20200322_1739"),
    ]

    operations = [
        migrations.AddField(
            model_name="hero",
            name="skills",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=100), default=[], size=None
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="hero",
            name="f2p_level",
            field=models.CharField(
                choices=[
                    ("F_00_STORY", "Story"),
                    ("F_02_THREE_STARS_STANDARD", "3* Standard Pool"),
                    ("F_03_THREE_STARS_LIMITED", "3* Limited Pool"),
                    ("F_04_FOUR_STARS_STANDARD", "4* Standard Pool"),
                    ("F_01_GRAIL", "Grail"),
                    ("F_05_FOUR_STARS_LIMITED", "4* Limited Pool"),
                    ("F_08_FIVE_STARS_STANDARD", "3* Standard Pool"),
                    ("F_09_FIVE_STARS_LIMITED", "3* Standard Pool"),
                ],
                max_length=25,
            ),
        ),
        migrations.AlterField(
            model_name="skill",
            name="f2p_levels",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    choices=[
                        ("F_00_STORY", "Story"),
                        ("F_02_THREE_STARS_STANDARD", "3* Standard Pool"),
                        ("F_03_THREE_STARS_LIMITED", "3* Limited Pool"),
                        ("F_04_FOUR_STARS_STANDARD", "4* Standard Pool"),
                        ("F_01_GRAIL", "Grail"),
                        ("F_05_FOUR_STARS_LIMITED", "4* Limited Pool"),
                        ("F_08_FIVE_STARS_STANDARD", "3* Standard Pool"),
                        ("F_09_FIVE_STARS_LIMITED", "3* Standard Pool"),
                    ],
                    max_length=25,
                ),
                size=None,
            ),
        ),
    ]
