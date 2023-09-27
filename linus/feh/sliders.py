from typing import List, NamedTuple

from .models import Hero, Skill


class Slider(NamedTuple):
    index: int
    title: str
    min: int
    max: int


def get_hero_stat_sliders(heroes: List[Hero]) -> List[Slider]:
    all_stats = [
        [
            "hp",
            [hero.hp for hero in heroes] + [hero.max_stats[0] for hero in heroes],
        ],
        [
            "atk",
            [hero.attack for hero in heroes] + [hero.max_stats[1] for hero in heroes],
        ],
        [
            "spd",
            [hero.speed for hero in heroes] + [hero.max_stats[2] for hero in heroes],
        ],
        [
            "def",
            [hero.defense for hero in heroes] + [hero.max_stats[3] for hero in heroes],
        ],
        [
            "res",
            [hero.resistance for hero in heroes] + [hero.max_stats[4] for hero in heroes],
        ],
        ["bst", [hero.bst for hero in heroes] + [hero.max_bst for hero in heroes]],
    ]

    stat_sliders = []
    for i, (title, stat) in enumerate(all_stats):
        stat_sliders.append(
            Slider(
                index=i,
                title=title,
                min=min(stat),
                max=max(stat),
            )
        )

    return stat_sliders


def get_skill_stat_sliders(skills: List[Skill]) -> List[Slider]:
    all_stats = [
        ["cost", 3, [skill.cost for skill in skills]],
        ["rarity", 5, [skill.rarity for skill in skills]],
    ]

    stat_sliders = []
    for i, (title, html_col_index, stat) in enumerate(all_stats):
        stat_sliders.append(
            Slider(
                index=html_col_index,
                title=title,
                min=min(stat),
                max=max(stat),
            )
        )

    return stat_sliders
