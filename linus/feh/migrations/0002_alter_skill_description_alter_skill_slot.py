# Generated by Django 5.2 on 2025-04-23 08:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("feh", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="skill",
            name="description",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="skill",
            name="slot",
            field=models.CharField(
                choices=[
                    ("W_01", "R Sword"),
                    ("W_02", "B Lance"),
                    ("W_03", "G Axe"),
                    ("W_11", "R Tome"),
                    ("W_12", "B Tome"),
                    ("W_13", "G Tome"),
                    ("W_14", "C Tome"),
                    ("W_15", "X Tome"),
                    ("W_21", "R Bow"),
                    ("W_22", "B Bow"),
                    ("W_23", "G Bow"),
                    ("W_24", "C Bow"),
                    ("W_25", "X Bow"),
                    ("W_31", "R Dagger"),
                    ("W_32", "B Dagger"),
                    ("W_33", "G Dagger"),
                    ("W_34", "C Dagger"),
                    ("W_35", "X Dagger"),
                    ("W_41", "R Dragon"),
                    ("W_42", "B Dragon"),
                    ("W_43", "G Dragon"),
                    ("W_44", "C Dragon"),
                    ("W_45", "X Dragon"),
                    ("W_51", "R Beast"),
                    ("W_52", "B Beast"),
                    ("W_53", "G Beast"),
                    ("W_54", "C Beast"),
                    ("W_55", "X Beast"),
                    ("W_04", "C Staff"),
                    ("W_05", "X Staff"),
                    ("W_71", "Assist"),
                    ("W_81", "Special"),
                    ("W_91", "A"),
                    ("W_91", "B"),
                    ("W_91", "C"),
                    ("W_94", "Sacred Seal"),
                ],
                max_length=15,
            ),
        ),
    ]
