from datetime import datetime, date, time

from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils import timezone
import pytz


def GetResetDate():
    d = date(2019, 1, 15)
    t = time(15, 0, 0, tzinfo=pytz.timezone("Asia/Singapore"))
    return datetime.combine(d, t)


ARENA_RESET_EPOCH = GetResetDate()


class AetherLiftForm(forms.Form):
    aether = forms.IntegerField(
        validators=[validators.MinValueValidator(0), validators.MaxValueValidator(1000)]
    )
    lift = forms.IntegerField(
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(100000),
        ],
        initial=11000,
    )
    reset_left = forms.IntegerField(
        validators=[validators.MinValueValidator(0), validators.MaxValueValidator(15)],
        initial=6,
    )

    # has_free_run = forms.BooleanField(required=False, initial=True)
    lift_gain = forms.IntegerField(
        initial=160,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(1000),
        ],
    )

    aether_storage_max = forms.IntegerField(
        initial=250,
        validators=[
            validators.MinValueValidator(100),
            validators.MaxValueValidator(1000),
        ],
    )

    aether_regen = forms.IntegerField(
        initial=70,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(1000),
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_time = timezone.now()
        epoch_distance = current_time - ARENA_RESET_EPOCH
        so_far = epoch_distance.days % 7
        remain = 6 - so_far
        self.fields["reset_left"].initial = remain
        self.fields["aether"].widget.attrs.update({"autofocus": "autofocus"})


class LucksackForm(forms.Form):
    orbs = forms.IntegerField(
        validators=[validators.MinValueValidator(0), validators.MaxValueValidator(1000)]
    )

    five_star_focus_chance_total = forms.FloatField(
        validators=[validators.MinValueValidator(0), validators.MaxValueValidator(1)],
        initial=0.03,
    )
    five_star_pitybreaker_chance_total = forms.FloatField(
        validators=[validators.MinValueValidator(0), validators.MaxValueValidator(1)],
        initial=0.03,
    )

    number_of_other_focus_units_with_the_same_color_as_target = forms.IntegerField(
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(10000),
        ],
        initial=0,
    )
    number_of_other_focus_units_with_different_color_than_target = forms.IntegerField(
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(10000),
        ],
        initial=2,
    )

    number_of_five_star_units_with_the_same_color_as_target = forms.IntegerField(
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(10000),
        ],
        initial=30,
    )

    number_of_five_star_units_with_different_color_than_target = forms.IntegerField(
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(10000),
        ],
        initial=100,
    )

    number_of_four_star_or_lower_units_with_the_same_color_as_target = (
        forms.IntegerField(
            validators=[
                validators.MinValueValidator(0),
                validators.MaxValueValidator(10000),
            ],
            initial=100,
        )
    )

    number_of_four_star_or_lower_units_with_different_color_than_target = (
        forms.IntegerField(
            validators=[
                validators.MinValueValidator(0),
                validators.MaxValueValidator(10000),
            ],
            initial=300,
        )
    )

    is_target_unit_already_in_summonable_pool = forms.BooleanField(
        required=False, initial=False
    )

    def clean(self):
        cleaned_data = super().clean()

        f1 = cleaned_data.get(
            "number_of_four_star_or_lower_units_with_the_same_color_as_target"
        )
        f2 = cleaned_data.get(
            "number_of_four_star_or_lower_units_with_different_color_than_target"
        )
        if f1 + f2 == 0:
            raise forms.ValidationError("Ensure at least one four star or lower units")

        f1 = cleaned_data.get("five_star_focus_chance_total")
        f2 = cleaned_data.get("five_star_pitybreaker_chance_total")
        if f1 + f2 > 1:
            raise forms.ValidationError(
                "Sum of focus and pitybreaker chances must be at most 1"
            )

        if cleaned_data.get("is_target_unit_already_in_summonable_pool"):
            f1 = cleaned_data.get(
                "number_of_five_star_units_with_the_same_color_as_target"
            )
            if f1 < 1:
                raise forms.ValidationError(
                    "if unit already in summonable pool, must exist at least one ssr unit with same color"
                )


class EmptyForm(forms.Form):
    pass


class PasswordForm(forms.Form):
    password = forms.CharField()

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password != "5*linus+10":
            raise ValidationError("Wrong password")
        return password
