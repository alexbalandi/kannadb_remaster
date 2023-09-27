from advanced_filters.admin import AdminAdvancedFiltersMixin
from django.contrib import admin

from . import models


@admin.register(models.Hero)
class HeroAdmin(AdminAdvancedFiltersMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "title",
        "movement_type",
        "weapon_type",
        "color",
        "hp",
        "attack",
        "speed",
        "defense",
        "resistance",
        "bst",
        "generation",
        "harmonized_skill",
    )

    search_fields = (
        "name",
        "title",
        "movement_type",
        "weapon_type",
        "color",
        "availability",
    )

    list_filter = (
        "movement_type",
        "weapon_type",
        "color",
        "availability",
        "book",
        "generation",
        "harmonized_skill",
    )
    # simple list filters

    # specify which fields can be selected in the advanced filter
    # creation form
    advanced_filter_fields = (
        "name",
        "title",
        "availability",
        "movement_type",
        "weapon_type",
        "color",
        "hp",
        "attack",
        "speed",
        "defense",
        "resistance",
        "bst",
        "book",
        "generation",
        "release_date",
        "harmonized_skill",
    )
