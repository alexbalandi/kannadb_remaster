import pickle
import ssl
import time
import urllib.parse
import urllib.request
import warnings

import certifi
from bs4 import BeautifulSoup


# Add retry logic here
def readURL(url, max_retries=5, initial_delay=2, rate_limit_delay=60):
    """
    Fetches URL content with retries for transient HTTP errors and rate limiting.

    Args:
        url: URL to fetch
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds for exponential backoff
        rate_limit_delay: Delay in seconds when rate limited (default 60 seconds)
    """
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    retries = 0
    delay = initial_delay
    while retries < max_retries:
        try:
            print(f"Attempt {retries + 1}/{max_retries}: Fetching {url}")
            response = urllib.request.urlopen(url, context=ssl_context, timeout=60)
            content = response.read()

            # Check for rate limit errors in XML response
            try:
                soup = BeautifulSoup(content, "lxml-xml")
                if soup.api and soup.api.error:
                    error_code = soup.api.error.get("code", "")
                    error_info = soup.api.error.get("info", "")
                    if "ratelimited" in error_code.lower() or "rate limit" in error_info.lower():
                        retries += 1
                        if retries < max_retries:
                            print(f"  Rate limit detected. Waiting {rate_limit_delay} seconds before retry...")
                            time.sleep(rate_limit_delay)
                            # Increase delay for subsequent rate limit hits
                            rate_limit_delay = min(rate_limit_delay * 1.5, 300)  # Cap at 5 minutes
                            continue
                        else:
                            raise ValueError(f"Rate limited after {max_retries} retries: {error_info}")
            except Exception:
                # If XML parsing fails, assume it's valid content
                pass

            return content

        except urllib.error.HTTPError as e:
            # Handle HTTP 429 (Too Many Requests) or other rate limit codes
            if e.code == 429 or (500 <= e.code < 600):
                retries += 1
                if retries < max_retries:
                    wait_time = rate_limit_delay if e.code == 429 else delay
                    print(f"  HTTP Error {e.code} ({e.reason}). Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    if e.code == 429:
                        rate_limit_delay = min(rate_limit_delay * 1.5, 300)
                    else:
                        delay *= 2
                else:
                    print(f"  HTTP Error {e.code} ({e.reason}). Max retries reached. Failing.")
                    raise
            else:
                print(f"  HTTP Error {e.code} ({e.reason}). Not retrying.")
                raise

        except Exception as e:
            retries += 1
            if retries < max_retries:
                print(f"  Network error ({type(e).__name__}: {e}). Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"  Network error ({type(e).__name__}: {e}). Max retries reached. Failing.")
                raise

    raise ConnectionError(f"Failed to fetch {url} after {max_retries} retries.")


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
    cargoquery = "https://feheroes.gamepedia.com/api.php?"
    # action=cargoqueryautocomplete&format=xml
    cargoFields = {"action": "cargoqueryautocomplete", "format": "xml"}
    cargoquery1 = cargoquery + urllib.parse.urlencode(cargoFields)
    # print(cargoquery1)
    curlXML = readURLSoup(cargoquery1, "lxml-xml")

    # Check for errors in the API response
    if curlXML.api.error:
        error_code = curlXML.api.error.get("code", "")
        error_info = curlXML.api.error.get("info", "")
        raise ValueError(f"API Error ({error_code}): {error_info}\n{curlXML}")

    allEntries = curlXML.api.cargoqueryautocomplete.contents
    tableNames = [e.attrs["main_table"] for e in allEntries]
    if table not in tableNames:
        raise ValueError(table, "not in", tableNames)
    # action=cargoqueryautocomplete&format=xml&tables=SummoningAvailability
    cargoFields["tables"] = table
    cargoquery2 = cargoquery + urllib.parse.urlencode(cargoFields)
    # print(cargoquery2)
    # Add small delay between verification requests
    time.sleep(0.5)
    curlXML = readURLSoup(cargoquery2, "lxml-xml")

    # Check for errors in the API response
    if curlXML.api.error:
        error_code = curlXML.api.error.get("code", "")
        error_info = curlXML.api.error.get("info", "")
        raise ValueError(f"API Error ({error_code}): {error_info}\n{curlXML}")

    allEntries = curlXML.api.cargoqueryautocomplete.contents
    fieldNames = [e.contents[0] for e in allEntries]
    for f in tableFields:
        f = f.split("=")[0]
        if f == "_rowID":
            continue
        fullName = table + "." + f
        if fullName not in fieldNames:
            raise ValueError(fullName, "not in", fieldNames)


# :eggplant:
def getRawDictFromTable(table, tableFields, baseFieldName, request_delay=1.0):
    """
    Fetches data from a table with pagination support.

    Args:
        table: Table name to query
        tableFields: List of fields to retrieve
        baseFieldName: Field name to use as the key
        request_delay: Delay in seconds between paginated requests (default 1.0)
    """
    verifyTableFields(table, tableFields)
    results = {}
    aliasedTableFields = [f.rsplit("=")[-1] for f in tableFields]
    if baseFieldName not in aliasedTableFields:
        raise ValueError(baseFieldName, "not in", tableFields)
    cargoquery = "https://feheroes.gamepedia.com/api.php?"
    cargoFields = {
        "action": "cargoquery",
        "format": "xml",
        "tables": table,
        "fields": ",".join(tableFields),
        "limit": 500,  # max the API gives us
        "offset": 0,  # increase this by 500 per curl
    }
    while True:
        cargoqueryRun = cargoquery + urllib.parse.urlencode(cargoFields)
        # print(cargoqueryRun)
        curlXML = readURLSoup(cargoqueryRun, "lxml-xml")

        # Check for errors in the API response
        if curlXML.api.error:
            error_code = curlXML.api.error.get("code", "")
            error_info = curlXML.api.error.get("info", "")
            raise ValueError(f"API Error ({error_code}): {error_info}\n{curlXML}")

        if curlXML.api.cargoquery is None:
            raise ValueError(curlXML)
        allEntries = curlXML.api.cargoquery.contents
        if len(allEntries) == 0:
            break
        print(table, cargoFields["offset"])
        for entry in allEntries:
            entryDict = entry.contents[0].attrs
            entryName = entryDict[baseFieldName]
            if entryName in results:
                warnings.warn(entryName + " is a duplicate", stacklevel=2)
            # print('added ' + entryName)
            results[entryName] = entryDict
        cargoFields["offset"] += 500
        # Add delay between paginated requests to avoid rate limiting
        if len(allEntries) == 500:  # Only delay if there might be more pages
            time.sleep(request_delay)
    return results


# because leenis likes double dicting :eggplant: :eggplant:
def getRawDoubleDictFromTable(table, tableFields, baseFieldName, secondaryFieldName, request_delay=1.0):
    """
    Fetches data from a table with pagination support, organizing into nested dictionaries.

    Args:
        table: Table name to query
        tableFields: List of fields to retrieve
        baseFieldName: Field name to use as the primary key
        secondaryFieldName: Field name to use as the secondary key
        request_delay: Delay in seconds between paginated requests (default 1.0)
    """
    verifyTableFields(table, tableFields)
    results = {}
    aliasedTableFields = [f.rsplit("=")[-1] for f in tableFields]
    if baseFieldName not in aliasedTableFields:
        raise ValueError(baseFieldName, "not in", tableFields)
    if secondaryFieldName not in aliasedTableFields:
        raise ValueError(secondaryFieldName, "not in", tableFields)

    cargoquery = "https://feheroes.gamepedia.com/api.php?"
    cargoFields = {
        "action": "cargoquery",
        "format": "xml",
        "tables": table,
        "fields": ",".join(tableFields),
        "limit": 500,  # max the API gives us
        "offset": 0,  # increase this by 500 per curl
    }
    while True:
        cargoqueryRun = cargoquery + urllib.parse.urlencode(cargoFields)
        # print(cargoqueryRun)
        curlXML = readURLSoup(cargoqueryRun, "lxml-xml")

        # Check for errors in the API response
        if curlXML.api.error:
            error_code = curlXML.api.error.get("code", "")
            error_info = curlXML.api.error.get("info", "")
            raise ValueError(f"API Error ({error_code}): {error_info}\n{curlXML}")

        if curlXML.api.cargoquery is None:
            raise ValueError(curlXML)
        allEntries = curlXML.api.cargoquery.contents
        if len(allEntries) == 0:
            break
        print(table, cargoFields["offset"])
        for entry in allEntries:
            entryDict = entry.contents[0].attrs
            entryName = entryDict[baseFieldName]
            secondaryName = entryDict[secondaryFieldName]
            if entryName in results:
                results[entryName][secondaryName] = entryDict
            else:
                results[entryName] = {secondaryName: entryDict}
        cargoFields["offset"] += 500
        # Add delay between paginated requests to avoid rate limiting
        if len(allEntries) == 500:  # Only delay if there might be more pages
            time.sleep(request_delay)
    return results


def getRawSkills():
    skillFields = [
        "_pageName=Page",
        "GroupName",
        "Name",
        "WikiName",
        "Scategory",
        "RefinePath",  # atk/def/res/spd/skill##
        "UseRange",
        "Description",
        "Required",  # WikiName Skill
        "Next",  # WikiName Skill
        "Exclusive",
        "SP",
        "CanUseMove",
        "CanUseWeapon",
        "Might",
        "StatModifiers",
        "Cooldown",
        "Properties",  # enemy_only and in case theres other useful stuff
    ]
    return getRawDictFromTable("Skills", skillFields, "WikiName")


def getRawWeaponUpgrades():
    upgradeFields = [
        "BaseWeapon",  # WikiName
        "UpgradesInto",  # WikiName
        "CostMedals",
        "CostStones",
        "CostDews",
        "StatModifiers",  # 5,2,0,0,0
        "BaseDesc",
        "AddedDesc",
    ]
    return getRawDictFromTable("WeaponUpgrades", upgradeFields, "UpgradesInto")


def getRawEvolutions():
    evoFields = [
        "BaseWeapon",  # WikiName
        "EvolvesInto",  # WikiName
        "CostMedals",
        "CostStones",
        "CostDew",
    ]
    return getRawDoubleDictFromTable("WeaponEvolutions", evoFields, "BaseWeapon", "EvolvesInto")


def getRawSeals():
    sealFields = [
        "Skill",
        "BadgeColor",
        "BadgeCost",
        "GreatBadgeCost",
        "SacredCoinCost",
    ]
    return getRawDictFromTable("SacredSealCosts", sealFields, "Skill")


def getRawUnits():
    unitFields = [
        "_pageID=PageID",
        "_pageName=Page",
        "Name",  # full name = Name:Title
        "Title",
        "WikiName",
        "Person",
        "Origin",
        # 'TagID',
        # 0-189, 190-316, 317-453, 454-593, 594-737
        "IntID",
        "Gender",
        "WeaponType",
        "MoveType",
        "GrowthMod",
        "Artist",
        # 'ActorEN',
        # 'ActorJP',
        "AdditionDate",
        "ReleaseDate",
        "Properties",
        "Description",
    ]
    return getRawDictFromTable("Units", unitFields, "WikiName")


def getRawUnitStats():
    statFields = [
        "WikiName",
        "Lv1HP5",
        "Lv1Atk5",
        "Lv1Spd5",
        "Lv1Def5",
        "Lv1Res5",
        "HPGR3",
        "AtkGR3",
        "SpdGR3",
        "DefGR3",
        "ResGR3",
    ]
    return getRawDictFromTable("UnitStats", statFields, "WikiName")


def getRawUnitSkills():
    unitSkillFields = [
        "WikiName",  # WikiName unit
        "skill",  # WikiName skill
        "skillPos",
        "defaultRarity",
        "unlockRarity",
    ]
    return getRawDoubleDictFromTable("UnitSkills", unitSkillFields, "WikiName", "skill")


def getLegendaryHeroes():
    legFields = [
        "_pageName=Page",
        "LegendaryEffect",
        # 'AllyBoostHP',
        # 'AllyBoostAtk',
        # 'AllyBoostSpd',
        # 'AllyBoostDef',
        # 'AllyBoostRes',
        "Duel",
    ]
    return getRawDictFromTable("LegendaryHero", legFields, "Page")


def getDuoHeroes():
    duoFields = [
        "_pageName=Page",
        "DuoSkill",
        "WikiSecondPerson",
        "WikiThirdPerson",
        "Duel",
    ]
    return getRawDictFromTable("DuoHero", duoFields, "Page")


def getMythicHeroes():
    mythicFields = [
        "_pageName=Page",
        # 'AllyBoostHP',
        # 'AllyBoostAtk',
        # 'AllyBoostSpd',
        # 'AllyBoostDef',
        # 'AllyBoostRes',
        "MythicEffect",
    ]
    return getRawDictFromTable("MythicHero", mythicFields, "Page")


def getHarmonizedHeroes():
    harmonizedFields = [
        "_pageName=Page",
        "HarmonizedSkill",
        "WikiSecondPerson",
        "WikiThirdPerson",
    ]
    return getRawDictFromTable("HarmonizedHero", harmonizedFields, "Page")


def getSummonFocusUnits():
    focusFields = ["_rowID=ID", "WikiName", "Unit", "Rarity"]
    return getRawDictFromTable("SummoningEventFocuses", focusFields, "ID")


def getSummoningAvailability():
    availFields = ["_rowID=ID", "_pageName=Page", "Rarity", "StartTime", "EndTime"]
    # use rowID as a primary key because sadfaec
    return getRawDictFromTable("SummoningAvailability", availFields, "ID")


def getDistributions():
    distFields = [
        "_pageName=Page",
        "Unit",
        "Rarity",
        "Source",
        "Amount",
        "Type",
        "StartTime",
        "EndTime",
    ]
    return getRawDictFromTable("Distributions", distFields, "Unit")


PHASES = 3


def CurlAll(phase, pkl_output_file="poro.pkl", request_delay=1.0):
    """
    Fetches all data for a given phase.

    Args:
        phase: Phase number (0, 1, or 2)
        pkl_output_file: Base filename for pickle output
        request_delay: Delay in seconds between requests (default 1.0)
    """
    assert phase in range(PHASES)
    pkl_output_file = "%s.%d" % (pkl_output_file, phase)
    # curl first think later, smurt
    if phase == 0:
        rawSkills = getRawSkills()
        time.sleep(request_delay)  # Delay between different table fetches
        rawUpgrades = getRawWeaponUpgrades()
        time.sleep(request_delay)
        rawEvolutions = getRawEvolutions()
        time.sleep(request_delay)
        rawUnitStats = getRawUnitStats()
    if phase == 1:
        rawUnitSkills = getRawUnitSkills()
    if phase == 2:
        rawUnits = getRawUnits()
        time.sleep(request_delay)
        rawSeals = getRawSeals()
        time.sleep(request_delay)
        rawLegHeroes = getLegendaryHeroes()
        time.sleep(request_delay)
        rawDuoHeroes = getDuoHeroes()
        time.sleep(request_delay)
        rawMythicHeroes = getMythicHeroes()
        time.sleep(request_delay)
        rawHarmonizedHeroes = getHarmonizedHeroes()
        time.sleep(request_delay)
        rawSummonFocusUnits = getSummonFocusUnits()
        time.sleep(request_delay)
        rawHeroAvails = getSummoningAvailability()
    # heroDistributions = getDistributions()

    with open(pkl_output_file, "wb") as f:
        p = pickle.Pickler(f)
        if phase == 0:
            p.dump(rawSkills)
            p.dump(rawUpgrades)
            p.dump(rawEvolutions)
            p.dump(rawUnitStats)
        if phase == 1:
            p.dump(rawUnitSkills)
        if phase == 2:
            p.dump(rawUnits)
            p.dump(rawSeals)
            p.dump(rawLegHeroes)
            p.dump(rawDuoHeroes)
            p.dump(rawMythicHeroes)
            p.dump(rawHarmonizedHeroes)
            p.dump(rawSummonFocusUnits)
            p.dump(rawHeroAvails)
            # p.dump(heroDistributions)
