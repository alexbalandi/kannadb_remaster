# Written by /u/Pororo#5569 (22 March 2020)
# Modified by Linus
# DEPRECATED
# TODO: make a proper version for poro_v2

import os.path
import pickle

from django.conf import settings


# Load the info from the pickled file.
def LoadPoro():
    file_root = os.path.join(settings.MEDIA_ROOT, "poro")
    filename = "poro.pkl"

    pkl_output_file = os.path.join(file_root, filename)

    with open(pkl_output_file, "rb") as f:
        up = pickle.Unpickler(f)
        weaponList = up.load()
        upgradableList = up.load()
        assistList = up.load()
        specialList = up.load()
        passiveList = up.load()
        heroList = up.load()

    # name              string
    # mod               string
    # full_name         string
    # categories        string[]
    # rarities          int[]
    # releaseDate       string
    # lvl_1_Stats       int[5][6][3]
    # lvl_40_Stats      int[5][6][3]
    # statArray         int[6]
    # weaponReqs        (Weapon,int,int)[]
    # skillReqs         (Skill,int,int)[]
    # duoSkill          string
    # color             string
    # weapon            string
    for hero in heroList:
        print("  Checking: ", hero)
        if hero.categories == []:
            print("  (!)", hero, "has no categories")
        if hero.rarities == []:
            print("(!)", hero, "has no rarities")
        if hero.releaseDate == "":
            print("  (!)", hero, "has no releaseDate")
        # if hero.lvl_1_Stats == emptyStats:
        hero_flat_lvl1_stats = sum(sum(hero.lvl_1_Stats, []), [])
        hero_flat_lvl40_stats = sum(sum(hero.lvl_40_Stats, []), [])
        if None in hero_flat_lvl1_stats:
            raise ValueError("  (!)", hero, "has corrupted level 1 Stats", hero_flat_lvl1_stats)
        if None in hero_flat_lvl40_stats:
            raise ValueError("  (!)", hero, "has corrupted level 40 Stats", hero_flat_lvl40_stats)
        if None in hero.statArray:
            raise ValueError("  (!)", hero, "has corrupted stat array", hero.statArray)
        if hero.weaponReqs == []:
            raise ValueError("  (!)", hero, "has no weapons")
        if hero.skillReqs == []:  # maskcina should trigger this
            if "Enigmatic Blade" in hero.mod or "Enigmatic_Blade" in hero.mod:
                print("  (.) Ignored maskcina exception for no skills")
            else:
                raise ValueError("  (!)", hero, "has no skills")
        if hero.isDuo() and hero.duoSkill == "":
            raise ValueError("  (!)", hero, "is marked as duo but has no duo skill")
        if hero.color == "":
            raise ValueError("  (!)", hero, "has no color")
        if hero.weapon == "":
            raise ValueError("  (!)", hero, "has no weapon type")
        if hero.move == "":
            raise ValueError("  (!)", hero, "has no move type")
        if hero.heroSrc == "":
            raise ValueError("  (!)", hero, "has no src type")

        print("  (+) hero emptiness check done")
        for weaponReq in hero.weaponReqs:
            weapon = weaponReq[0]
            if weapon not in weaponList:
                print("  (!)", weapon, "not in the weaponList")
        for skillReq in hero.skillReqs:
            skill = skillReq[0]
            if skill in assistList:
                continue
            if skill in specialList:
                continue
            if skill in passiveList:
                continue
            raise ValueError("  (!)", skill, "not in any of the skill lists")
        print("  (+) hero skill check complete")

    print("(+) All hero checks complete!")

    for weapon in upgradableList:
        if weapon not in weaponList:
            raise ValueError("  (!)", weapon, "has a duplicate in the upgradableList")
        if len(weapon.refines) == 0:
            raise ValueError("  (!)", weapon, "is marked as upgradable without any refines")

    print("(+) Checked upgradable list for duplicates")

    for weapon in weaponList:
        if weapon.url == "" or weapon.url is None:
            raise ValueError("  (!)", weapon, "has no url")

    for skill in assistList:
        if skill.url == "" or skill.url is None:
            raise ValueError("  (!)", skill, "has no url")

    for skill in specialList:
        if skill.url == "" or skill.url is None:
            raise ValueError("  (!)", skill, "has no url")

    for skill in passiveList:
        if skill.url == "" or skill.url is None:
            raise ValueError("  (!)", skill, "has no url")

    print("(+) Checked skill and weapon URLs")

    print("PoropickleChecker done")

    return dict(
        weapons=weaponList,
        upgradables=upgradableList,
        assists=assistList,
        specials=specialList,
        passives=passiveList,
        heroes=heroList,
    )
