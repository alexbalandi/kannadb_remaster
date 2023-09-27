import time
from datetime import date
from time import strptime

from django.core.management.base import BaseCommand

from linus.feh.management.commands.curl_heroes import GetPklHeroURLFile, GetPklOutputFile
from linus.feh.models import AVAILABILITY, COLOR, F2P_LEVEL_OVERRIDE, MOVEMENT_TYPE, WEAPON_TYPE
from linus.feh.poro.poroimagecurler import GetKannaURLs

from ... import models

AV_MAP = dict(
    Normal=AVAILABILITY.STANDARD,
    Mythic=AVAILABILITY.MYTHIC,
    GHB=AVAILABILITY.GHB,
    Special=AVAILABILITY.SPECIAL,
    Story=AVAILABILITY.STORY,
    TT=AVAILABILITY.TT,
    Legendary=AVAILABILITY.LEGENDARY,
    Duo=AVAILABILITY.DUO,
    Harmonized=AVAILABILITY.HARMONIZED,
    Ascended=AVAILABILITY.ASCENDANT,
    Rearmed=AVAILABILITY.REARMED,
)

MV_MAP = dict(
    Infantry=MOVEMENT_TYPE.INFANTRY,
    Armored=MOVEMENT_TYPE.ARMOR,
    Cavalry=MOVEMENT_TYPE.CAVALRY,
    Flying=MOVEMENT_TYPE.FLYING,
)

WP_MAP = {
    "Red Sword": WEAPON_TYPE.R_SWORD,
    "Blue Lance": WEAPON_TYPE.B_LANCE,
    "Green Axe": WEAPON_TYPE.G_AXE,
    "Red Tome": WEAPON_TYPE.R_TOME,
    "Blue Tome": WEAPON_TYPE.B_TOME,
    "Green Tome": WEAPON_TYPE.G_TOME,
    "Colorless Tome": WEAPON_TYPE.C_TOME,
    "Red Dagger": WEAPON_TYPE.R_DAGGER,
    "Blue Dagger": WEAPON_TYPE.B_DAGGER,
    "Green Dagger": WEAPON_TYPE.G_DAGGER,
    "Colorless Dagger": WEAPON_TYPE.C_DAGGER,
    "Red Bow": WEAPON_TYPE.R_BOW,
    "Blue Bow": WEAPON_TYPE.B_BOW,
    "Green Bow": WEAPON_TYPE.G_BOW,
    "Colorless Bow": WEAPON_TYPE.C_BOW,
    "Red Beast": WEAPON_TYPE.R_BEAST,
    "Blue Beast": WEAPON_TYPE.B_BEAST,
    "Green Beast": WEAPON_TYPE.G_BEAST,
    "Colorless Beast": WEAPON_TYPE.C_BEAST,
    "Red Breath": WEAPON_TYPE.R_DRAGON,
    "Blue Breath": WEAPON_TYPE.B_DRAGON,
    "Green Breath": WEAPON_TYPE.G_DRAGON,
    "Colorless Breath": WEAPON_TYPE.C_DRAGON,
    "Colorless Staff": WEAPON_TYPE.C_STAFF,
}

WP_EXPANSION = {
    "Dragon": [
        "Red Breath",
        "Blue Breath",
        "Green Breath",
        "Colorless Breath",
    ]
}

COLOR_MAP = dict(
    Red=COLOR.RED,
    Blue=COLOR.BLUE,
    Green=COLOR.GREEN,
    Colorless=COLOR.COLORLESS,
)


SLOT_MAP = dict(
    passivea=WEAPON_TYPE.A_SLOT,
    passiveb=WEAPON_TYPE.B_SLOT,
    passivec=WEAPON_TYPE.C_SLOT,
    assist=WEAPON_TYPE.ASSIST,
    seal=WEAPON_TYPE.SACRED_SEAL,
    special=WEAPON_TYPE.SPECIAL,
    sacredseal=WEAPON_TYPE.SACRED_SEAL,
)

WEAPON_SLOT_MAP = {
    WEAPON_TYPE.R_SWORD: WEAPON_TYPE.R_SWORD,
    WEAPON_TYPE.B_LANCE: WEAPON_TYPE.B_LANCE,
    WEAPON_TYPE.G_AXE: WEAPON_TYPE.G_AXE,
    WEAPON_TYPE.R_TOME: WEAPON_TYPE.R_TOME,
    WEAPON_TYPE.B_TOME: WEAPON_TYPE.B_TOME,
    WEAPON_TYPE.G_TOME: WEAPON_TYPE.G_TOME,
    WEAPON_TYPE.C_TOME: WEAPON_TYPE.C_TOME,
    WEAPON_TYPE.R_BOW: WEAPON_TYPE.X_BOW,
    WEAPON_TYPE.B_BOW: WEAPON_TYPE.X_BOW,
    WEAPON_TYPE.G_BOW: WEAPON_TYPE.X_BOW,
    WEAPON_TYPE.C_BOW: WEAPON_TYPE.X_BOW,
    WEAPON_TYPE.R_DAGGER: WEAPON_TYPE.X_DAGGER,
    WEAPON_TYPE.B_DAGGER: WEAPON_TYPE.X_DAGGER,
    WEAPON_TYPE.G_DAGGER: WEAPON_TYPE.X_DAGGER,
    WEAPON_TYPE.C_DAGGER: WEAPON_TYPE.X_DAGGER,
    WEAPON_TYPE.R_DRAGON: WEAPON_TYPE.X_DRAGON,
    WEAPON_TYPE.B_DRAGON: WEAPON_TYPE.X_DRAGON,
    WEAPON_TYPE.G_DRAGON: WEAPON_TYPE.X_DRAGON,
    WEAPON_TYPE.C_DRAGON: WEAPON_TYPE.X_DRAGON,
    WEAPON_TYPE.R_BEAST: WEAPON_TYPE.X_BEAST,
    WEAPON_TYPE.B_BEAST: WEAPON_TYPE.X_BEAST,
    WEAPON_TYPE.G_BEAST: WEAPON_TYPE.X_BEAST,
    WEAPON_TYPE.C_BEAST: WEAPON_TYPE.X_BEAST,
    WEAPON_TYPE.C_STAFF: WEAPON_TYPE.X_STAFF,
}


class Command(BaseCommand):
    help = "Import Heroes from porocode."

    def handle(self, *args, **options):
        all_data = GetKannaURLs(GetPklOutputFile(), GetPklHeroURLFile())

        heroes = all_data["heroes"]

        hero_objs = []
        allstats = [[], [], [], [], []]
        total_heroes = len(heroes)
        current_hero = 0
        for hero in heroes:
            print(current_hero, "/", total_heroes)
            current_hero += 1
            if not hero.releaseDate:
                # Not summonable
                continue

            finalstat = hero.statArray
            release_date = strptime(hero.releaseDate, "%Y-%m-%d")

            skills = []
            for skillreq in hero.getMaxSkills():
                skills.append(skillreq.name)

            boonbanes = []
            for i in range(5):
                stats = hero.lvl_40_Stats[-1][i]
                res = ""
                if stats[1] - stats[0] == 4:
                    res = res + "-"
                if stats[2] - stats[1] == 4:
                    res = res + "+"
                boonbanes.append(res)

            origin = hero.origin
            """
      # The following actually resides in a method of my model
      if hero.iconURL:
        icon_url = hero.iconURL
        icon_data = urlretrieve(icon_url) # image_url is a URL to an image
        image_field_data = ImageFile(open(icon_data[0], 'rb'))
      else:
        image_field_data = None
      """

            hero_objs.append(
                (
                    models.Hero(
                        name=hero.name,
                        title=hero.mod,
                        stripped_name=hero.wikiName,
                        availability=AV_MAP[hero.heroSrc],
                        movement_type=MV_MAP[hero.move],
                        weapon_type=WP_MAP[hero.weapon],
                        color=COLOR_MAP[hero.color],
                        hp=finalstat[0],
                        attack=finalstat[1],
                        speed=finalstat[2],
                        defense=finalstat[3],
                        resistance=finalstat[4],
                        bst=finalstat[5],
                        origin_game=origin,
                        rarities=hero.rarities,
                        release_date=date.fromtimestamp(time.mktime(release_date)),
                        gamepedia_url=hero.url,
                        skills=skills,
                        boonbanes=boonbanes,
                        gender=hero.gender,
                        is_dancer=hero.isDancer,
                        has_resplendent=("resplendent" in hero.properties),
                        season=hero.season,
                        harmonized_skill=hero.harmonizedSkill or hero.duoSkill or None,
                        artist=hero.artist,
                        # icon_image=image_field_data,
                    ),
                    hero,
                )
            )

            for i in range(5):
                allstats[i].append(finalstat[i])

        # Commit everything.
        models.Hero.objects.all().delete()
        for hero, _ in hero_objs:
            hero.save()

        # Next import skills
        skills = all_data["skills"]
        skill_objs = []
        skill_map = {}

        # This is a very disgusting hack to overcome porofeature
        combin = []
        for skill in skills:
            if skill.isRefine or skill.isEnemyOnly or skill.slot == "sacredseal":
                continue
            combin.append(
                (
                    "skill",
                    skill,
                    False,
                )
            )

        seals = all_data["seals"]
        for seal in seals:
            combin.append(("seal", seal.skill, seal.isMax))

        skill_slot = None

        for skilltype, skill, ismax in combin:
            description = skill.desc

            if skilltype == "seal":
                skill_slot = WEAPON_TYPE.SACRED_SEAL
            elif skill.slot != "weapon":
                # Note: ignoring stuff like captain skills
                # TODO: potentially revisit this
                if skill.slot not in SLOT_MAP:
                    continue
                skill_slot = SLOT_MAP[skill.slot]
                # mt = None
                # srange = None
            else:
                # May be wrong: e.g., breaths are 4 color
                # assert len(skill.weaponPerms) == 1
                if skill.weaponPerms:
                    skill_slot = WEAPON_SLOT_MAP[WP_MAP[skill.weaponPerms[0]]]
                    # mt = skill.mt
                    # srange = skill.range
                    for refine in skill.refines:
                        if refine.desc:
                            description = "{0}\n\n[Original effect before refine]\n{1}".format(refine.desc, description)

            cleaned_weapon_perms = []
            for weapon_perm in skill.weaponPerms:
                if weapon_perm in WP_EXPANSION:
                    cleaned_weapon_perms.extend(WP_EXPANSION[weapon_perm])
                else:
                    cleaned_weapon_perms.append(weapon_perm)

            weapon_perms = sorted(list(set([WEAPON_SLOT_MAP[WP_MAP[wp]] for wp in cleaned_weapon_perms])))
            movement_perms = sorted(list(set([MV_MAP[mv] for mv in skill.movePerms])))

            if not skill_slot:
                print('Skill has no weapon perms: "%s". Skipping...' % skill.name)
                continue

            skill_obj = models.Skill(
                name=skill.name,
                stripped_name=skill.wikiName,
                description=description,
                slot=skill_slot,
                cost=skill.cost,
                is_prf=skill.isPrf,
                is_max=ismax,
                f2p_levels=[],
                rarity=5,
                # mt=mt,
                # range=srange,
                release_date=None,
                book=None,
                availabilities=[],
                heroes=[],
                hero_stripped_names=[],
                gamepedia_url=skill.url,
                weapon_permissions=weapon_perms,
                movement_permissions=movement_perms,
            )
            skill_objs.append(skill_obj)
            if skilltype != "seal":
                skill_map[skill_obj.stripped_name] = skill_obj

        # Fill the hero relevant datas.
        for hero, raw_hero in hero_objs:
            for skillreq in raw_hero.skillReqs:
                raw_skill = skillreq.skill
                skill_obj = skill_map[raw_skill.wikiName]
                if skillreq.isMax:
                    skill_obj.is_max = True

                # Hack for gamepedia ebil deeds:
                if hero.rarities == []:
                    hero.rarities = [5]

                actual_rarity = max(skillreq.unlockRarity, min(hero.rarities))

                skill_obj.availabilities.append(hero.availability)
                # if not hero.icon_image:
                #  raise Exception('Missing image for hero %s (%s)' % (hero.name, hero.title))
                skill_obj.heroes.append(
                    "{0}@{1}@{2}@{3}".format(hero.f2p_level, hero.availability, hero.title, hero.name)
                )
                skill_obj.hero_stripped_names.append(hero.stripped_name)

                skill_obj.f2p_levels.append(hero.f2p_level)

                skill_obj.rarity = min(skill_obj.rarity, actual_rarity)
                if skill_obj.release_date is None or skill_obj.release_date > hero.release_date:
                    skill_obj.release_date = hero.release_date
                    skill_obj.book = hero.book

        # Fix the availabilities and heroes and commit
        for skill in skill_objs:
            skill.availabilities = sorted(set(skill.availabilities))
            skill.heroes = sorted(skill.heroes)

            # f2p level is complicated.
            f2p_set = set(skill.f2p_levels)
            for level, overrides in F2P_LEVEL_OVERRIDE.items():
                if level in f2p_set:
                    for disc in overrides:
                        f2p_set.discard(disc)
            skill.f2p_levels = sorted(f2p_set)

        models.Skill.objects.all().delete()
        for skill in skill_objs:
            skill.save()
