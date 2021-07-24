# Written by /u/Pororo#5569 (22 March 2020)
# Modified by Linus
# DEPRECATED

from operator import itemgetter

# type              string
# name              string
# mt                int
# range             int
# isPrf             boolean
# cost              int
# desc              string
# isRefinable       boolean
# refines           Refine[]
# url               string
# slot              string
# evolutions        [Weapon]
class Weapon(object):   
    def __init__(self):   
        self.type = ""
        self.name = ""
        self.mt = 0
        self.range = 0
        self.isPrf = False
        self.cost = 0
        self.desc = ""
        self.isRefinable = False
        self.refines = []
        self.url = ""
        self.slot = 'WEAPON'
        self.evolutions = []
    def __str__(self):
        return self.name    
    def __repr__(self):
        return self.name    
   

# feel free to adjust the __str__ and __repr__ kek
# desc              string
# stats             string
class Refine(object):
    def __init__(self):
        self.desc = ""
        self.stats = ""
    def __str__(self):
        return " ".join(self.stats)    
    def __repr__(self):
        return " ".join(self.stats)      
 

# Skill := Assist, Special, Passive
# name              string
# isPrf             bool
# cost              int
# range             int
# desc              string
# slot              string
# cd                int
# url               string
class Skill(object):
    def __init__(self):
        self.name = ""
        self.isPrf = False
        self.cost = 0
        self.range = 0
        self.descs = ""
        self.slot = ""
        self.cd = 0
        self.url = ""
    def __str__(self):
        return self.name    
    def __repr__(self):
        return self.name    
 

# name              string
# mod               string
# full_name         string
# categories        string[]
# rarities          int[]
# releaseDate       string
# lvl_1_Stats       int[5][6][3]
# lvl_40_Stats      int[5][6][3]
# statArray         int[6]
# weaponReqs        [Weapon,int,int,bool][]
# skillReqs         [Skill,int,int,bool][]
#   weapon|skill
#   defaultStars
#   unlockStars
#   isMax
#       weaps: 5* or evolved from a 5*
#       skills: final skill of that skill slot
# duoSkill          string
# color             string
# weapon            string
# heroSrc           string
# move              string
# url
class Hero(object):

    STAT_HP = 0
    STAT_ATK = 1
    STAT_SPD = 2
    STAT_DEF = 3
    STAT_RES = 4
    STAT_TOT = 5    

    def __init__(self):
        self.name = ""
        self.mod = ""
        self.full_name = ""
        self.categories = []
        self.rarities = []
        self.releaseDate = ""
        self.lvl_1_Stats = [[None, None, None] * 6 for i in range(5)]
        self.lvl_40_Stats = [[None, None, None] * 6 for i in range(5)]
        self.statArray = [None,None,None,None,None,None]
        self.weaponReqs = []
        self.skillReqs = []
        self.duoSkill = ""
        self.color = ""
        self.weapon = ""
        self.heroSrc = ""
        self.move = ""
        self.url = ""

    def isDuo(self):
        return "Duo Heroes" in self.categories
    def isTT(self):
        return self.heroSrc == "TT"
    def isGHB(self):
        return self.heroSrc == "GHB"

    def isRed(self):
        return self.getColor() == "Red"
    def isBlue(self):
        return self.getColor() == "Blue"
    def isGreen(self):
        return self.getColor() == "Green"
    def isColorless(self):
        return self.getColor() == "Colorless"
    
    def getColor(self):
        return self.color

    def getWeaponType(self):
        if self.weapon in ['Beast', 'Bow', 'Stave', 'Dagger', 'Dragonstone',]:
            return '{0} {1}'.format(self.color, self.weapon)
        return self.weapon        

    def getMove(self):
        return self.move

    def isF2P(self):
        return 3 in self.rarities or 4 in self.rarities

    def isGrail(self):
        return self.isTT() or self.isGHB()

    def getWeapons(self):
        return [req[0] for req in self.weaponReqs]

    def getSkills(self):
        return [req[0] for req in self.skillReqs]

    # return all 5 star weapons
    def getMaxWeapons(self):
        return [wr[0] for wr in self.weaponReqs if wr[2] == 5]   

    def getMaxSkills(self):
        return [sr[0] for sr in self.skillReqs if sr[3]]

    def getStatTuple(self, stat, stars = 5, isLvl40 = True):
        if isLvl40:
            return self.lvl_40_Stats[stars-1][stat]
        else:
            return self.lvl_1_Stats[stars-1][stat]

    # 0 = bane, 2 = boon
    def getStat(self, stat, bane_neut_boon=1, stars=5, isLvl40 = True):
        return self.getStatTuple(stat, stars, isLvl40)[bane_neut_boon]

    def getBST(self):
        return self.getStat(self.STAT_TOT)

    def getNeutralStats(self, lvl_40 = True):
        if lvl_40:
            return [t[1] for t in self.lvl_40_Stats[4]]
        else:
            return [t[1] for t in self.lvl_1_Stats[4]]


    def getPullableRarities(self):
        return self.rarities

    # shitty code but whatever its all shitty anyway lulll
    def getStatOrder(self):
        statTuples = [(stat, (5 - stat) + 100 * self.getStat(stat, isLvl40 = False)) for stat in range(5)]
        sortedTuples = sorted(statTuples, key=itemgetter(1), reverse=True)
        return [sortedTuple[0] for sortedTuple in sortedTuples]

    def getStatOrderString(self):
        return [self.getStatString(stat) for stat in self.getStatOrder()]

    def getStatString(self, stat):
        if stat < 0 or stat > 5:
            return None
        else:
            return ["HP", "ATK", "SPD", "DEF", "RES"][stat]                

    def getStatHelpString(self):
        print("0 => STAT_HP ")
        print("1 => STAT_ATK")
        print("2 => STAT_SPD")
        print("3 => STAT_DEF")
        print("4 => STAT_RES")
        print("5 => STAT_TOT")
        return

    def getSrc(self):
        return self.heroSrc

    # must be called by the parser 
    # before hero is ready for export
    def finalize(self):
        # because leenis hates Flame_Emperor
        self.name = self.name.replace("_", " ")
        self.mod = self.mod.replace("_", " ")
        self.full_name = self.full_name.replace("_", " ")
        # extract neutral stats and weapontype for easy fetching
        self.statArray = [bnb[1] for bnb in self.lvl_40_Stats[4]]
        self.weapon = self.weaponReqs[0][0].type
        
        # categories => color info
        if "Red Heroes" in self.categories:
            self.color = "Red"
        elif "Blue Heroes" in self.categories:
            self.color = "Blue"
        elif "Green Heroes" in self.categories:
            self.color = "Green"
        elif "Colorless Heroes" in self.categories:
            self.color = "Colorless"
        else:
            raise ValueError(self, "has no colour in", self.categories)
       
        # categories => source info
        if "Duo Heroes" in self.categories:
            self.heroSrc = "Duo"
        elif "Tempest Trials Heroes" in self.categories:
            self.heroSrc = "TT"
        elif "Grand Heroes" in self.categories:
            self.heroSrc = "GHB"
        elif "Legendary Heroes" in self.categories:
            self.heroSrc = "Legendary"
        elif "Mythic Heroes" in self.categories:
            self.heroSrc = "Mythic"
        elif "Story Heroes" in self.categories:
            self.heroSrc = "Story"
        elif "Special Heroes" in self.categories:
            self.heroSrc = "Special"
        else:
            self.heroSrc = "Normal"
            
        # categories => movement type info
        if "Infantry Heroes" in self.categories:
            self.move = "Infantry"
        elif "Cavalry Heroes" in self.categories:
            self.move = "Cavalry"
        elif "Armored Heroes" in self.categories:
            self.move = "Armor"
        elif "Flying Heroes" in self.categories:
            self.move = "Flying"
        else:
            raise ValueError("  (!)", self, "has no src type", self.categories)

        # add isMax boolean to final weapon/skills
        
        # assume all 5* weaps and their derivatives are max
        for wr in self.weaponReqs:
            if wr[2] == 5:
                wr[3] = True
                origWeap = wr[0]                
                for newWeap in origWeap.evolutions:
                    nwr = wr[:]
                    nwr[0] = newWeap
                    self.weaponReqs.append(nwr)                    

        # hack: assume last skill of each slot is final
        allSlots = set([sr[0].slot for sr in self.skillReqs])
        for slot in allSlots:
            slotSkillReqs = [sr for sr in self.skillReqs if sr[0].slot == slot]
            slotSkillReqs[-1][3] = True

    def __str__(self):
        return self.full_name    

    def __repr__(self):
        return self.full_name    
