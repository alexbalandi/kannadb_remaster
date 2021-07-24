from django.conf.urls import url
from django.urls import path
from django.views.decorators.cache import cache_page
from django.views.generic.base import TemplateView

from linus.feh.views import (
    lucksack_calculator,
    HeroesList,
    CurlHeroes,
    SkillsList,
    MaxOnlySkillsList,
    CurlHeroesDoPhaseBase,
    HeroesListAjax,
    SkillsListAjaxMax,
    SkillsListAjax,
)

from .views import (
    aether_lift_calculator,
)


app_name = "feh"
urlpatterns = [
    path("ar_calculator/", view=aether_lift_calculator, name="arcalc"),
    path("lucksack_calculator/", view=lucksack_calculator, name="lucksackcalc"),
    path("heroes/", view=cache_page(60 * 10)(HeroesList.as_view()), name="heroes_list"),
    path(
        "heroes_ajax.json",
        view=cache_page(60 * 10)(HeroesListAjax),
        name="heroes_list_ajax",
    ),
    path("curl_heroes/", CurlHeroes.as_view(), name="curl_heroes"),
    url(
        "^curl_heroes_do/(?P<phase>\d+)/(?P<password>[0-9a-fA-F]+)/$",
        view=cache_page(60)(CurlHeroesDoPhaseBase.as_view()),
        name="curl_heroes_do",
    ),
    path(
        "skills/",
        view=cache_page(60 * 10)(MaxOnlySkillsList.as_view()),
        name="skills_list",
    ),
    path(
        "max_skills_ajax.json",
        view=cache_page(60 * 10)(SkillsListAjaxMax),
        name="skills_list_max_ajax",
    ),
    path(
        "skills_ajax.json",
        view=cache_page(60 * 10)(SkillsListAjax),
        name="skills_list_ajax",
    ),
    path(
        "skills/all/",
        view=cache_page(60 * 10)(SkillsList.as_view()),
        name="skills_list_all",
    ),
    path(
        "",
        view=cache_page(60 * 10)(
            TemplateView.as_view(template_name="feh/welcome.html")
        ),
        name="home",
    ),
]
