from typing import Any, List, NamedTuple, Optional

from django.templatetags.static import static

from .models import Hero, Skill


class Filter(NamedTuple):
    id: str
    content: List[Any]
    btn_class: str
    title: Optional[str]


class Slider(NamedTuple):
    index: int
    title: str
    min: int
    max: int


def get_f2p_filter(heroes: List[Hero]) -> Filter:
    f2p_levels = sorted(
        set(
            [
                (hero.f2p_level, ("img", hero.f2p_level_icon, hero.f2p_level_human))
                for hero in heroes
            ]
        )
    )
    return Filter(
        id="f2p",
        content=f2p_levels,
        btn_class="btn-choose-any",
        title=None,
    )


def get_stat_filter(heroes: List[Hero]) -> Filter:
    max_stats = [
        ["normal", ("txt", "5*+0 Lv40", "Stats at 5* rarity Lv 40")],
        [
            "adjusted",
            (
                "txt",
                "Adjusted",
                "Same as 5*+0 Lv40, but infantry units with 10 flowers get +1"
                " to all stats, and resplendent get +2 to all stats",
            ),
        ],
        [
            "max",
            (
                "txt",
                "MAX",
                "Maximum possible unsupported no skills stat: 5*+10 Lv40 with"
                " the appropriate boon, all flowers, resplendent",
            ),
        ],
        ["none", ("txt", "None", "Hide this")],
    ]

    return Filter(
        id="statdisplay",
        content=max_stats,
        btn_class="btn-stat-cycle",
        title="Stat Display",
    )


def get_movement_type_filter(heroes: List[Hero]) -> Filter:
    movement_types = sorted(
        set(
            [
                (
                    hero.movement_type,
                    ("img", hero.movement_type_icon, hero.movement_type_human),
                )
                for hero in heroes
            ]
        )
    )

    return Filter(
        id="movement-type",
        content=movement_types,
        btn_class="btn-choose-any",
        title=None,
    )


def get_weapon_type_filter(heroes: List[Hero]) -> Filter:
    weapon_types = sorted(
        set(
            [
                (
                    hero.weapon_type,
                    ("img", hero.weapon_type_icon, hero.weapon_type_human),
                )
                for hero in heroes
            ]
        )
    )

    return Filter(
        id="weapon-type",
        content=weapon_types,
        btn_class="btn-choose-any",
        title=None,
    )


def get_season_filter(heroes: List[Hero]) -> Filter:
    # Unlike others, this is hard coded to maintain a good order.
    # Maybe one day we'll remove this hard coding.
    season_types = [
        "Fire",
        "Water",
        "Wind",
        "Earth",
        "Light",
        "Dark",
        "Astra",
        "Anima",
    ]
    seasons = [
        (
            season,
            (
                "img",
                static("images/icons/Icon_Season_{0}.png".format(season)),
                season,
            ),
        )
        for season in season_types
    ]

    return Filter(
        id="season",
        content=seasons,
        btn_class="btn-choose-any",
        title=None,
    )


def get_availability_filter(heroes: List[Hero]) -> Filter:
    availabilities = sorted(
        set([(hero.availability, ("txt", hero.availability_human)) for hero in heroes])
    )

    # Availability
    return Filter(
        id="availability",
        content=availabilities,
        btn_class="btn-choose-any",
        title="Source",
    )


def get_origin_game_filter(heroes: List[Hero]) -> Filter:
    origin_games = sorted(
        set(
            [
                (hero.game_code, ("img", hero.game_icon, hero.game_human))
                for hero in heroes
            ]
        )
    )

    return Filter(
        id="origin_game",
        content=origin_games,
        btn_class="btn-choose-any",
        title="Game",
    )


def get_book_filter(heroes: List[Hero]) -> Filter:
    books = sorted(set([(hero.book, ("txt", hero.book_human)) for hero in heroes]))

    return Filter(
        id="book",
        content=books,
        btn_class="btn-choose-any",
        title="Book",
    )


def get_generation_filter(heroes: List[Hero]) -> Filter:
    generations = sorted(
        set([(hero.generation, ("txt", hero.generation_human)) for hero in heroes])
    )

    return Filter(
        id="generation",
        content=generations,
        btn_class="btn-choose-any",
        title="Generation",
    )


def get_gender_filter(heroes: List[Hero]) -> Filter:
    gender = sorted(set([(hero.gender, ("txt", hero.gender)) for hero in heroes]))

    return Filter(
        id="gender",
        content=gender,
        btn_class="btn-choose-any",
        title="Gender",
    )


def get_true_false_filter(id: str, title: Optional[str]) -> Filter:
    content = [
        ["true", ("txt", "yes")],
        ["false", ("txt", "no")],
    ]
    return Filter(
        id=id,
        content=content,
        btn_class="btn-choose-any",
        title=title,
    )


def get_skill_slot_filter(skills: List[Skill]) -> Filter:
    slot_types = sorted(
        set([(skill.slot, ("img", skill.slot_icon)) for skill in skills])
    )

    return Filter(
        id="slot",
        content=slot_types,
        btn_class="btn-choose-any",
        title="Skill type",
    )


def get_weapon_permission_filter(skills: List[Skill]) -> Filter:
    weapon_types = sorted(
        list(set(sum([skill.weapon_permissions for skill in skills], [])))
    )
    weapon_types = [
        (
            weapon_type,
            ("img", static("images/icons/ICON_{0}.png".format(weapon_type))),
        )
        for weapon_type in weapon_types
    ]
    return Filter(
        id="weapon_permissions",
        content=weapon_types,
        btn_class="btn-choose-any",
        title=None,
    )


def get_movement_permission_filter(skills: List[Skill]) -> Filter:
    movement_types = sorted(
        list(set(sum([skill.movement_permissions for skill in skills], [])))
    )
    movement_types = [
        (
            movement_type,
            ("img", static("images/icons/ICON_{0}.png".format(movement_type))),
        )
        for movement_type in movement_types
    ]

    return Filter(
        id="movement_permissions",
        content=movement_types,
        btn_class="btn-choose-any",
        title=None,
    )
