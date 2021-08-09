from linus.feh.sliders import get_hero_stat_sliders, get_skill_stat_sliders
import sys
from datetime import date

from django.core.cache import cache
from django.core.exceptions import SuspiciousOperation
from django.http.response import JsonResponse
from django.shortcuts import redirect
from django.urls.base import reverse
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.edit import FormView

from linus.feh.lucksack_calc import FehSnipeProbability
from linus.feh.management.commands.curl_heroes import GetPklOutputFile
from linus.feh.models import AVAILABILITY, MOVEMENT_TYPE, WEAPON_TYPE
from linus.feh.poro import porocurler_v2
from linus.feh.poro.porocurler_v2 import CurlAll
from linus.feh.poro.poroparser_v2 import LoadPoro

from . import forms, models
from .filters import (
    Filter,
    get_availability_filter,
    get_book_filter,
    get_f2p_filter,
    get_gender_filter,
    get_generation_filter,
    get_movement_permission_filter,
    get_movement_type_filter,
    get_origin_game_filter,
    get_season_filter,
    get_skill_slot_filter,
    get_stat_filter,
    get_true_false_filter,
    get_weapon_permission_filter,
    get_weapon_type_filter,
)


MULTIPLIER_MAX = 2


def AetherCost(lift):
    return min(50, (lift + 99) // 100 + 9)


def Pot(lift):
    return min(10, ((lift // 100) + 10) // 5)


def Calc(aether, lift, resets, lift_gain=100, aether_max=200, aether_regen=50):
    res = []
    current_aether = aether
    current_lift = lift
    res.append("Aether: {0}, Lift: {1}".format(current_aether, current_lift))

    pot_gains = []
    matches_multi = {}
    for i in range(1, MULTIPLIER_MAX + 1):
        matches_multi[i] = 0

    for x in range(resets + 1):
        res.append("")
        res.append("Start of day {0}/{1}".format(x, resets))
        if x:
            res.append("Aether regen daily.")
            current_aether += aether_regen
            res.append("Aether: {0}, Lift: {1}".format(current_aether, current_lift))
            current_aether = min(current_aether, aether_max)

        # Do Free Run
        # if has_free_run or x:
        #  pot_q = Pot(current_lift)
        #  res.append('>>>Free run. Pay 0. Get {0} from pots'.format(pot_q))
        #  current_aether += pot_q
        #  current_aether = min(current_aether, aether_max)
        #  current_lift += lift_gain
        #  pot_gains.append(pot_q)
        #  res.append('Aether: {0}, Lift: {1}'.format(current_aether, current_lift))

        # Do double runs as much as you can, except last day.
        while current_aether >= AetherCost(current_lift):
            if x < resets and current_aether + aether_regen <= aether_max:
                # be lazy and do it later.
                break

            cost = AetherCost(current_lift)
            pot = Pot(current_lift)
            multiplier = 1
            if cost * 2 <= current_aether:
                # do dubble match.
                multiplier = 2

            res.append(
                ">>>{2}x run. Pay {0}. Get {1} from pots".format(
                    cost * multiplier, pot * multiplier, multiplier
                )
            )

            matches_multi[multiplier] += 1

            current_aether -= cost * multiplier
            current_aether += pot * multiplier
            for _ in range(multiplier):
                pot_gains.append(pot)
            current_aether = min(current_aether, aether_max)
            current_lift += lift_gain * multiplier
            res.append("Aether: {0}, Lift: {1}".format(current_aether, current_lift))

    # How many pots can I miss?
    can_miss = 0
    if len(pot_gains) >= 2:
        spare = current_aether - pot_gains[-1]
        i = len(pot_gains) - 2
        while i >= 0:
            if spare - pot_gains[i] >= 0:
                spare -= pot_gains[i]
                can_miss += 2
                i -= 1
            elif spare - (pot_gains[i] - pot_gains[i] / 2) >= 0:
                spare -= pot_gains[i] - pot_gains[i] / 2
                can_miss += 1
                break
            else:
                break

    return res, current_aether, current_lift, can_miss, matches_multi


class AetherLiftCalculator(FormView):
    template_name = "feh/calculator.html"
    form_class = forms.AetherLiftForm
    res = ""

    def get_context_data(self, *args, **kwargs):
        context = FormView.get_context_data(self, *args, **kwargs)
        context["res"] = self.res
        return context

    def form_valid(self, form):
        log, aether, lift, can_miss, matches = Calc(
            form.cleaned_data["aether"],
            form.cleaned_data["lift"],
            form.cleaned_data["reset_left"],
            form.cleaned_data["lift_gain"],
            form.cleaned_data["aether_storage_max"],
            form.cleaned_data["aether_regen"],
        )
        matches_keys = matches.keys()
        matches_result = []
        for match_key in sorted(matches_keys):
            matches_result.append(dict(multiplier=match_key, num=matches[match_key]))
        self.res = dict(
            log="\n".join(log),
            aether=aether,
            lift=lift,
            can_miss=can_miss,
            matches=sum(matches.values()),
            breakdown=matches_result,
        )
        return self.get(form)


aether_lift_calculator = AetherLiftCalculator.as_view()


class LucksackCalculator(FormView):
    template_name = "feh/lucksack.html"
    form_class = forms.LucksackForm
    res = ""

    def get_context_data(self, *args, **kwargs):
        context = FormView.get_context_data(self, *args, **kwargs)
        context["res"] = self.res
        return context

    def form_valid(self, form):

        orbs = form.cleaned_data.get("orbs")

        ssr_focus = form.cleaned_data.get("five_star_focus_chance_total")
        ssr_pity = form.cleaned_data.get("five_star_pitybreaker_chance_total")

        ssr_f_sc = form.cleaned_data.get(
            "number_of_other_focus_units_with_the_same_color_as_target"
        )
        ssr_f_wc = form.cleaned_data.get(
            "number_of_other_focus_units_with_different_color_than_target"
        )

        ssr_n_sc = form.cleaned_data.get(
            "number_of_five_star_units_with_the_same_color_as_target"
        )
        ssr_n_wc = form.cleaned_data.get(
            "number_of_five_star_units_with_different_color_than_target"
        )

        com_n_sc = form.cleaned_data.get(
            "number_of_four_star_or_lower_units_with_the_same_color_as_target"
        )
        com_n_wc = form.cleaned_data.get(
            "number_of_four_star_or_lower_units_with_different_color_than_target"
        )

        already_in_pool = form.cleaned_data.get(
            "is_target_unit_already_in_summonable_pool"
        )

        total_focus_units = 1 + ssr_f_sc + ssr_f_wc
        total_ssr_units = ssr_n_sc + ssr_n_wc
        total_com_units = com_n_sc + com_n_wc

        units = [
            (1, "red", 1, ssr_focus / total_focus_units),
            (2, "red", 1, ssr_f_sc * ssr_focus / total_focus_units),
            (3, "blue", 1, ssr_f_wc * ssr_focus / total_focus_units),
            # (4, 'red', 1, ssr_n_sc * ssr_pity / total_ssr_units),
            (5, "blue", 1, ssr_n_wc * ssr_pity / total_ssr_units),
            (6, "red", 0, com_n_sc * (1.0 - ssr_focus - ssr_pity) / total_com_units),
            (7, "blue", 0, com_n_wc * (1.0 - ssr_focus - ssr_pity) / total_com_units),
        ]
        if already_in_pool:
            units.append((1, "red", 1, ssr_pity / total_ssr_units))
            units.append((4, "red", 1, (ssr_n_sc - 1) * ssr_pity / total_ssr_units))
        else:
            units.append((4, "red", 1, ssr_n_sc * ssr_pity / total_ssr_units))

        sys.setrecursionlimit(10000)
        sackchance = FehSnipeProbability(orbs, units, 1)
        self.res = list(enumerate(sackchance))

        return self.get(form)


lucksack_calculator = LucksackCalculator.as_view()


def GetRandomAxeInfantry():
    return (
        models.Hero.objects.filter(
            weapon_type=WEAPON_TYPE.G_AXE,
            movement_type=MOVEMENT_TYPE.INFANTRY,
            availability=AVAILABILITY.STANDARD,
        )
        .exclude(name="Linus")
        .order_by("?")[0]
    )


def GetRandomUnit():
    return models.Hero.objects.all().order_by("?")[0]


def HeroesListAjax(request):
    heroes = list(models.Hero.objects.all().order_by("name", "title"))
    data = []
    for hero in heroes:
        herodata = {}
        herodata["full_name"] = dict(
            name=hero.name,
            title=hero.title,
            full_name=hero.full_name,
            icon=hero.availability_icon,
            human=hero.availability_human,
            url=hero.gamepedia_url,
        )
        # hero_icon_url=hero.icon_image.url)
        herodata["f2p_level"] = dict(
            name=hero.f2p_level,
            icon=hero.f2p_level_icon,
            title=hero.f2p_level_human,
        )
        herodata["weapon_type"] = dict(
            name=hero.weapon_type,
            icon=hero.weapon_type_icon,
            title=hero.weapon_type_human,
        )
        herodata["movement_type"] = dict(
            name=hero.movement_type,
            icon=hero.movement_type_icon,
            title=hero.movement_type_human,
        )

        herodata["boonbanes"] = hero.boonbanes

        pairs = [
            (hero.stats(), "stats"),
            (hero.max_stats, "max_stats"),
            (hero.adjusted_stats, "adjusted_stats"),
        ]
        for attrib, atname in pairs:
            ctxl = []
            for i in range(len(attrib)):
                ctxl.append(dict(value=attrib[i], bb=hero.boonbanes[i]))
            herodata[atname] = ctxl

        herodata["bst"] = hero.bst
        herodata["max_bst"] = hero.max_bst
        herodata["adjusted_bst"] = hero.adjusted_bst

        herodata["generation"] = hero.generation
        herodata["release_date"] = dict(
            display=hero.release_date.strftime("%-d %b %Y"),
            sortplay=hero.release_date.strftime("%Y-%m-%d"),
        )

        # herodata['weapon_type'] = hero.weapon_type
        # herodata['movement_type'] = hero.movement_type
        # herodata['f2p_level'] = hero.f2p_level
        herodata["book"] = hero.book

        herodata["availability"] = hero.availability
        herodata["skills"] = hero.skills
        herodata["origin_game"] = dict(
            name=hero.game_code,
            icon=hero.game_icon,
            title=hero.game_human,
        )
        herodata["stripped_name"] = hero.stripped_name
        herodata["gender"] = hero.gender
        herodata["is_dancer"] = hero.is_dancer
        herodata["StandardDeviation"] = "%.3f" % hero.StandardDeviation

        herodata["availability_human"] = hero.availability_human
        herodata["has_resplendent"] = hero.has_resplendent
        herodata["season"] = hero.season
        herodata["harmonized_skill"] = hero.harmonized_skill
        herodata["artist"] = hero.artist
        herodata["alias"] = hero.alias

        data.append(herodata)

    return JsonResponse(dict(data=data))


class KannadbListBase(TemplateView):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["rival"] = GetRandomAxeInfantry()
        context["virus"] = GetRandomUnit()
        heroes = list(models.Hero.objects.all().order_by("name", "title"))
        context["heroes"] = heroes
        return context


class HeroesList(KannadbListBase):
    template_name = "feh/heroes.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        heroes = context["heroes"]

        context["stats"] = get_hero_stat_sliders(heroes)

        context["filters"] = [
            # Stat display
            get_stat_filter(heroes),
            # Title for filter section
            Filter(
                id="dummy",
                content=[],
                btn_class="dummy",
                title="Filters",
            ),
            get_f2p_filter(heroes),
            get_movement_type_filter(heroes),
            get_weapon_type_filter(heroes),
            get_season_filter(heroes),
            get_availability_filter(heroes),
            get_true_false_filter(id="dancer", title="Dancer"),
            get_true_false_filter(id="resplendent", title="Resplendent"),
            get_origin_game_filter(heroes),
            get_book_filter(heroes),
            get_generation_filter(heroes),
            get_gender_filter(heroes),
        ]

        return context


def GenerateCurlPassword(phase):
    key = (
        23591735139048247645
        * (phase + 2427342347)
        * int(date.today().strftime("%Y%m%d"))
    )
    return key


class CurlHeroes(FormView):
    template_name = "feh/refresh.html"
    form_class = forms.PasswordForm
    res = ""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = "CURL HEROES"
        return context

    def form_valid(self, form):
        return redirect(
            reverse(
                "feh:curl_heroes_do",
                kwargs=dict(phase=0, password=GenerateCurlPassword(phase=0)),
            )
        )


class CurlHeroesDoPhaseBase(RedirectView):
    phase = None  # Fill this.

    def get_redirect_url(self, *args, **kwargs):
        phase = int(self.kwargs["phase"])
        assert phase in range(porocurler_v2.PHASES + 1)
        password = self.kwargs["password"]
        if password != GenerateCurlPassword(phase):
            # probably poron doing something fishy
            raise SuspiciousOperation()

        if phase < porocurler_v2.PHASES:
            CurlAll(phase, GetPklOutputFile())
        else:
            LoadPoro(GetPklOutputFile())
            cache.clear()

        if phase == porocurler_v2.PHASES:
            # all done
            return reverse("feh:heroes_list")
        else:
            return reverse(
                "feh:curl_heroes_do",
                kwargs=dict(phase=phase + 1, password=GenerateCurlPassword(phase + 1)),
            )


def SkillsListDo(skills):
    data = []
    for skill in skills:
        skilldata = {}
        skilldata["detailscontrol"] = ""
        skilldata["name"] = dict(name=skill.name, url=skill.gamepedia_url)
        skilldata["slot"] = dict(name=skill.slot, icon=skill.slot_icon)
        skilldata["cost"] = skill.cost
        skilldata["icons"] = skill.f2p_levels_icons
        skilldata["rarity"] = skill.rarity
        skilldata["release_date"] = dict(
            display=skill.release_date.strftime("%-d %b %Y")
            if skill.release_date
            else "",
            sortplay=skill.release_date.strftime("%Y-%m-%d")
            if skill.release_date
            else "",
        )
        skilldata["heroes"] = skill.display_heroes
        skilldata["description"] = skill.description
        skilldata["is_max"] = skill.is_max
        skilldata["is_prf"] = skill.is_prf
        skilldata["f2p_levels"] = skill.f2p_levels
        # skilldata['slot'] = skill.slot
        skilldata["book"] = skill.book
        skilldata["usablebyicons"] = []
        if not skill.is_prf:
            skilldata["usablebyicons"] += skill.weapon_permissions_icons
            skilldata["usablebyicons"] += skill.movement_permissions_icons()

        skilldata["weapon_permissions"] = skill.weapon_permissions
        skilldata["movement_permissions"] = skill.movement_permissions
        skilldata["stripped_name"] = skill.stripped_name
        skilldata["hero_stripped_names"] = skill.hero_stripped_names
        data.append(skilldata)

        """
      {% for skill in skills%}
        <tr>
          <td>{% if not skill.is_prf %}Usable by:
            {% for skill_icon in skill.weapon_permissions_icons %}
              <img height="30pt" src="{{ skill_icon }}">
            {% endfor %}
            {% for skill_icon in skill.movement_permissions_icons %}
              <img height="30pt" src="{{ skill_icon }}">
            {% endfor %}{% endif %}</td>
          <td>{{ skill.weapon_permissions }}</td>
          <td>{{ skill.movement_permissions }}</td>
          <td>{{ skill.stripped_name }}</td>
          <td>{% for hero in skill.hero_stripped_names %}{{ hero }}{% endfor %}</td>
        </tr>
      {% endfor %}
    """

    return JsonResponse(dict(data=data))


def SkillsListAjaxMax(request):
    return SkillsListDo(models.Skill.objects.all().filter(is_max=True).order_by("name"))


def SkillsListAjax(request):
    return SkillsListDo(models.Skill.objects.all().order_by("name"))


class SkillsList(TemplateView):
    template_name = "feh/skills.html"
    JUST_MAX = False

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        skills = models.Skill.objects.all().order_by("name")
        context["skills"] = skills

        ajax_url_name = "feh:skills_list_ajax"
        if self.JUST_MAX:
            skills = skills.filter(is_max=True)
            ajax_url_name = "feh:skills_list_max_ajax"
        context["ajax_url_name"] = ajax_url_name

        skills = list(skills)
        heroes = list(models.Hero.objects.all().order_by("name", "title"))
        context["heroes"] = heroes

        context["stats"] = get_skill_stat_sliders(skills)

        context["filters"] = []
        if not self.JUST_MAX:
            context["filters"].append(
                get_true_false_filter(id="max", title="Max skills only?")
            )

        context["filters"].extend(
            [
                get_true_false_filter(
                    id="prf",
                    title="Prf",
                ),
                get_f2p_filter(heroes),
                get_skill_slot_filter(skills),
                get_book_filter(heroes),
                # Title for filter section
                Filter(
                    id="dummy",
                    content=[],
                    btn_class="dummy",
                    title="Who can learn?",
                ),
                get_movement_permission_filter(skills),
                get_weapon_permission_filter(skills),
            ]
        )
        return context


class MaxOnlySkillsList(SkillsList):
    JUST_MAX = True
