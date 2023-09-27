class Skill(object):
    def __init__(self):
        self.name = ""
        self.wikiName = ""  # gamepedia base key
        self.isEnemyOnly = False  # rokkr and stuff
        self.isRefine = False
        self.refineType = ""  # for refines
        self.isPrf = False
        self.isSeal = False  # e.g. QR
        self.cost = 0  # SP cost
        self.range = 0  # weaps, assist
        self.desc = ""
        self.slot = ""
        self.cd = 0  # specials
        self.url = ""  # full pedia url
        self.page = ""  # pedia page
        self.pageID = None  # int: pageID
        # these two are still stored in string form atm
        self.required = []  # skills required
        self.next = []  # next skill in chain

        # Infantry|Armored|Cavalry|Flying
        self.movePerms = []  # equippable movetypes
        # Red|Blue|Green|Colorless
        # Sword|Lance|Axe|Bow|Dagger|Tome|Staff|Breath|Beast
        self.weaponPerms = []  # equippable weapypes
        self.properties = []
        self.isEnemyOnly = False
        self.refines = []  # for weaps
        self.evolutions = []  # for weaps
        self.stats = "0,0,0,0,0"  # HP/A/S/D/R
        self.baseWeap = []  # for refines only

    def __str__(self):
        if self.isRefine:
            return self.wikiName
        else:
            return self.name

    def __repr__(self):
        return self.__str__()


class Refine(object):
    def __init__(self):
        self.skill = None  # refined weap
        self.statChange = ""  # stat changes
        self.refinePath = ""  # skill1/skill2/stats
        self.desc = ""  # changed desc if any

    def __str__(self):
        return self.skill.wikiName

    def __repr__(self):
        return self.__str__()


class Seal(object):
    def __init__(self):
        self.skill = None  # the underlying skill
        self.badgeColor = ""
        self.badgeCost = 0
        self.greatbadgeCost = 0
        self.coinCost = 0
        self.isMax = False  # as far as seals are concerned

    def __str__(self):
        return "Seal(%s)" % str(self.skill)

    def __repr__(self):
        return self.__str__()


class Hero(object):
    def __init__(self):
        self.name = ""
        # default to big number/6 in case its a new hero
        self.intID = 9999
        self.book = 6
        self.mod = ""
        self.full_name = ""
        self.releaseDate = ""
        self.url = ""
        self.page = ""
        self.iconURL = None
        # 1 for each star, stat
        self.lvl_1_Stats = [[(None, None, None) for i in range(5)] for j in range(5)]
        # 1 extra row per star for total
        self.lvl_40_Stats = [[(None, None, None) for i in range(6)] for j in range(5)]
        self.statArray = [None, None, None, None, None, None]
        # weaponReqs has been folded into skillReqs
        self.skillReqs = []

        self.color = ""
        # Red|Blue|Green|Colorless
        # Sword|Lance|Axe|Bow|Dagger|Tome|Staff|Breath|Beast
        self.weapon = ""
        # Infantry|Armored|Cavalry|Flying
        self.move = ""

        self.artist = ""
        self.gender = ""
        self.desc = ""
        self.origin = ""
        self.heroSrc = ""
        self.duel = 0  # for legendaries/duos
        self.season = ""  # for mythics/legs
        self.duoSkill = ""
        self.harmonizedSkill = ""
        self.rarities = []
        self.avails = []
        self.properties = []
        self.isDancer = False
        self.isRearmed = False
        # Calculated via growth rates
        self.generation = 0
        self.isTrainee = False
        self.isVeteran = False
        self.isAdvanced = False

    def getSkills(self):
        return [s.skill for s in self.skillReqs]

    def getWeapons(self):
        return [s for s in self.getSkills() if s.slot == "weapon"]

    def getPrfs(self):
        return [s for s in self.getSkills() if s.isPrf]

    def getMaxSkills(self):
        return [s.skill for s in self.skillReqs if s.isMax]

    def getMaxWeapons(self):
        return [s for s in self.getMaxSkills() if s.slot == "weapon"]

    def __str__(self):
        return self.full_name

    def __repr__(self):
        return self.__str__()


class SkillReq(object):
    def __init__(self):
        self.skill = None
        self.slot = ""
        # 0 means it does not come by default
        self.defaultRarity = 0
        self.unlockRarity = 0
        self.isMax = False

    def __str__(self):
        result = str((self.slot, self.skill, self.unlockRarity))
        if self.isMax:
            return "MAX" + result
        else:
            return result

    def __repr__(self):
        return self.__str__()


class Availability(object):
    def __init__(self):
        self.rarity = 0
        # GMT/UTC times
        self.startTime = None
        self.endTime = None

    def __str__(self):
        return str((self.rarity, self.startTime, self.endTime))

    def __repr__(self):
        return self.__str__()
