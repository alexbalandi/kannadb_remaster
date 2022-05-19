import os
import pickle
import urllib.parse
import urllib.request
import warnings

from bs4 import BeautifulSoup

import pycurl


# not stored to file
def readURL(url):
    url = urllib.request.urlopen(url)
    return url.read()
def readURLSoup(url, parser):
    return BeautifulSoup(readURL(url), parser)


def tryStrToInt(intStr):
    if not intStr:
        warnings.warn("NoneType submitted to tryStrToInt", stacklevel=2)
        return 0
    if intStr.isnumeric():
        return int(intStr)
    else:
        return 0

# https://feheroes.gamepedia.com/wiki/Special:CargoQuery
# TODO: Don't need to repeatedly verify by fetching all tablenames
def verifyTableFields(table, tableFields):
    cargoquery = 'https://feheroes.gamepedia.com/api.php?'
    # action=cargoqueryautocomplete&format=xml
    cargoFields = {
        'action'    :   'cargoqueryautocomplete',
        'format'    :   'xml'
    }
    cargoquery1 = cargoquery + urllib.parse.urlencode(cargoFields)
    # print(cargoquery1)
    curlXML = readURLSoup(cargoquery1, 'lxml-xml')
    allEntries = curlXML.api.cargoqueryautocomplete.contents
    tableNames = [e.attrs["main_table"] for e in allEntries]
    if not table in tableNames:
        raise ValueError(table, "not in", tableNames)
    # action=cargoqueryautocomplete&format=xml&tables=SummoningAvailability
    cargoFields["tables"] = table
    cargoquery2 = cargoquery + urllib.parse.urlencode(cargoFields)
    # print(cargoquery2)
    curlXML = readURLSoup(cargoquery2, 'lxml-xml')
    allEntries = curlXML.api.cargoqueryautocomplete.contents
    fieldNames = [e.contents[0] for e in allEntries]
    for f in tableFields:
        f = f.split("=")[0]
        if f == "_rowID":
            continue
        fullName = table + "." + f
        if not fullName in fieldNames:
            raise ValueError(fullName, "not in", fieldNames)

# :eggplant:
def getRawDictFromTable(table, tableFields, baseFieldName):
    verifyTableFields(table, tableFields)
    results = {}
    aliasedTableFields = [f.rsplit("=")[-1] for f in tableFields]
    if not baseFieldName in aliasedTableFields:
        raise ValueError(baseFieldName, "not in", tableFields)
    cargoquery = 'https://feheroes.gamepedia.com/api.php?'
    cargoFields = {
        'action'    :   'cargoquery',
        'format'    :   'xml',
        'tables'    :   table,
        'fields'    :   ",".join(tableFields),
        'limit'     :   500, # max the API gives us
        'offset'    :   0    # increase this by 500 per curl
    }
    while True:
        cargoquery += urllib.parse.urlencode(cargoFields)
        # print(cargoquery)
        curlXML = readURLSoup(cargoquery, 'lxml-xml')

        if curlXML.api.cargoquery == None:
            raise ValueError(curlXML)
        allEntries = curlXML.api.cargoquery.contents
        if len(allEntries) == 0:
            break
        print(table, cargoFields['offset'])
        for entry in allEntries:
            entryDict = entry.contents[0].attrs
            entryName = entryDict[baseFieldName]
            if entryName in results:
                warnings.warn(entryName + " is a duplicate", stacklevel=2)
            # print('added ' + entryName)
            results[entryName] = entryDict
        cargoFields['offset'] += 500
    return results

# because leenis likes double dicting :eggplant: :eggplant:
def getRawDoubleDictFromTable(table, tableFields, baseFieldName, secondaryFieldName):
    verifyTableFields(table, tableFields)
    results = {}
    aliasedTableFields = [f.rsplit("=")[-1] for f in tableFields]
    if not baseFieldName in aliasedTableFields:
        raise ValueError(baseFieldName, "not in", tableFields)
    if not secondaryFieldName in aliasedTableFields:
        raise ValueError(secondaryFieldName, "not in", tableFields)

    cargoquery = 'https://feheroes.gamepedia.com/api.php?'
    cargoFields = {
        'action'    :   'cargoquery',
        'format'    :   'xml',
        'tables'    :   table,
        'fields'    :   ",".join(tableFields),
        'limit'     :   500, # max the API gives us
        'offset'    :   0    # increase this by 500 per curl
    }
    while True:
        cargoquery += urllib.parse.urlencode(cargoFields)
        curlXML = readURLSoup(cargoquery, 'lxml-xml')

        if curlXML.api.cargoquery == None:
            raise ValueError(curlXML)
        allEntries = curlXML.api.cargoquery.contents
        if len(allEntries) == 0:
            break
        print(table, cargoFields['offset'])
        for entry in allEntries:
            entryDict = entry.contents[0].attrs
            entryName = entryDict[baseFieldName]
            secondaryName = entryDict[secondaryFieldName]
            if entryName in results:
                results[entryName][secondaryName] = entryDict
            else:
                results[entryName] = {secondaryName: entryDict}
        cargoFields['offset'] += 500
    return results

def getRawSkills():
    skillFields = [
        '_pageName=Page',
        'GroupName',
        'Name',
        'WikiName',
        'Scategory',
        'RefinePath',       # atk/def/res/spd/skill##
        'UseRange',
        'Description',
        'Required',         # WikiName Skill
        'Next',             # WikiName Skill
        'Exclusive',
        'SP',
        'CanUseMove',
        'CanUseWeapon',
        'Might',
        'StatModifiers',
        'Cooldown',
        'Properties'        # enemy_only and in case theres other useful stuff
    ]
    return getRawDictFromTable('Skills', skillFields, 'WikiName')

def getRawWeaponUpgrades():
    upgradeFields = [
        'BaseWeapon',       # WikiName
        'UpgradesInto',     # WikiName
        'CostMedals',
        'CostStones',
        'CostDews',
        'StatModifiers',    # 5,2,0,0,0
        'BaseDesc',
        'AddedDesc'
    ]
    return getRawDictFromTable('WeaponUpgrades', upgradeFields, 'UpgradesInto')

def getRawEvolutions():
    evoFields = [
        'BaseWeapon',      # WikiName
        'EvolvesInto',     # WikiName
        'CostMedals',
        'CostStones',
        'CostDew'
    ]
    return getRawDoubleDictFromTable('WeaponEvolutions', evoFields, 'BaseWeapon', 'EvolvesInto')

def getRawSeals():
    sealFields = [
        'Skill',
        'BadgeColor',
        'BadgeCost',
        'GreatBadgeCost',
        'SacredCoinCost'
    ]
    return getRawDictFromTable('SacredSealCosts', sealFields, 'Skill')

def getRawUnits():
    unitFields = [
        '_pageID=PageID',
        '_pageName=Page',
        'Name',             # full name = Name:Title
        'Title',
        'WikiName',
        'Person',
        'Origin',
        # 'TagID',
        # 'IntID',
        'Gender',
        'WeaponType',
        'MoveType',
        'GrowthMod',
        'Artist',
        # 'ActorEN',
        # 'ActorJP',
        'AdditionDate',
        'ReleaseDate',
        'Properties',
        'Description'
    ]
    return getRawDictFromTable('Units', unitFields, 'WikiName')

def getRawUnitStats():
    statFields = [
        'WikiName',
        'Lv1HP5',
        'Lv1Atk5',
        'Lv1Spd5',
        'Lv1Def5',
        'Lv1Res5',
        'HPGR3',
        'AtkGR3',
        'SpdGR3',
        'DefGR3',
        'ResGR3',
    ]
    return getRawDictFromTable('UnitStats', statFields, 'WikiName')

def getRawUnitSkills():
    unitSkillFields = [
        'WikiName',         # WikiName unit
        'skill',            # WikiName skill
        'skillPos',
        'defaultRarity',
        'unlockRarity'
    ]
    return getRawDoubleDictFromTable('UnitSkills', unitSkillFields, 'WikiName', 'skill' )

def getLegendaryHeroes():
    legFields = [
        '_pageName=Page',
        'LegendaryEffect',
        # 'AllyBoostHP',
        # 'AllyBoostAtk',
        # 'AllyBoostSpd',
        # 'AllyBoostDef',
        # 'AllyBoostRes',
        'Duel'
    ]
    return getRawDictFromTable('LegendaryHero', legFields, 'Page')

def getDuoHeroes():
    duoFields = [
        '_pageName=Page',
        'DuoSkill',
        'WikiSecondPerson',
        'WikiThirdPerson',
        'Duel'
    ]
    return getRawDictFromTable('DuoHero', duoFields, 'Page')

def getMythicHeroes():
    mythicFields = [
        '_pageName=Page',
        # 'AllyBoostHP',
        # 'AllyBoostAtk',
        # 'AllyBoostSpd',
        # 'AllyBoostDef',
        # 'AllyBoostRes',
        'MythicEffect'
    ]
    return getRawDictFromTable('MythicHero', mythicFields, 'Page')

def getHarmonizedHeroes():
    harmonizedFields = [
        '_pageName=Page',
        'HarmonizedSkill',
        'WikiSecondPerson',
        'WikiThirdPerson'
    ]
    return getRawDictFromTable('HarmonizedHero', harmonizedFields, 'Page')

def getSummonFocusUnits():
    focusFields = [
        '_rowID=ID',
        'WikiName',
        'Unit',
        'Rarity'
    ]
    return getRawDictFromTable('SummoningEventFocuses', focusFields, 'ID')

def getSummoningAvailability():
    availFields = [
        '_rowID=ID',
        '_pageName=Page',
        'Rarity',
        'StartTime',
        'EndTime'
    ]
    # use rowID as a primary key because sadfaec
    return getRawDictFromTable('SummoningAvailability', availFields, 'ID')

def getDistributions():
    distFields = [
        '_pageName=Page',
        'Unit',
        'Rarity',
        'Source',
        'Amount',
        'Type',
        'StartTime',
        'EndTime'
    ]
    return getRawDictFromTable('Distributions', distFields, 'Unit')


PHASES = 3

def CurlAll(phase, pkl_output_file = 'poro.pkl'):
    assert phase in range(PHASES)
    pkl_output_file = "%s.%d"%(pkl_output_file, phase)
    # curl first think later, smurt
    if (phase == 0):
        rawSkills = getRawSkills()
        rawUpgrades = getRawWeaponUpgrades()
        rawEvolutions = getRawEvolutions()
        rawUnitStats = getRawUnitStats()
    if (phase == 1):
        rawUnitSkills = getRawUnitSkills()
    if (phase == 2):
        rawUnits = getRawUnits()
        rawSeals = getRawSeals()
        rawLegHeroes = getLegendaryHeroes()
        rawDuoHeroes = getDuoHeroes()
        rawMythicHeroes = getMythicHeroes()
        rawHarmonizedHeroes = getHarmonizedHeroes()
        rawSummonFocusUnits = getSummonFocusUnits()
        rawHeroAvails = getSummoningAvailability()
    # heroDistributions = getDistributions()

    with open(pkl_output_file, 'wb') as f:
        p = pickle.Pickler(f)
        if (phase == 0):
            p.dump(rawSkills)
            p.dump(rawUpgrades)
            p.dump(rawEvolutions)
            p.dump(rawUnitStats)
        if (phase == 1):
            p.dump(rawUnitSkills)
        if (phase == 2):
            p.dump(rawUnits)
            p.dump(rawSeals)
            p.dump(rawLegHeroes)
            p.dump(rawDuoHeroes)
            p.dump(rawMythicHeroes)
            p.dump(rawHarmonizedHeroes)
            p.dump(rawSummonFocusUnits)
            p.dump(rawHeroAvails)
            # p.dump(heroDistributions)
