# Written by /u/Pororo#5569 (22 March 2020)
# Modified by Linus
# DEPRECATED

import os.path
import pickle
import re
import sys
import urllib.parse

from bs4 import BeautifulSoup
import certifi
from django.conf import settings
import unidecode

from config.settings.base import APPS_DIR
import pycurl

from .poroclasses import Weapon, Refine, Skill, Hero
import warnings

# Give the filename to which the output will be placed.
def CurlAll():
    #sys.stdout.reconfigure(encoding='utf-8')
    debugMode = False

    output_file_root = os.path.join(settings.MEDIA_ROOT, 'poro')

    if not os.path.isdir(output_file_root):
        os.mkdir(output_file_root)

    filename = 'poro.pkl'

    pkl_output_file = os.path.join(output_file_root, filename)

    file_root = str(APPS_DIR('heroes_curl'))
    heroFolder = os.path.join(file_root, 'heroes')
    skillFolder = os.path.join(file_root, 'skills')
    wikiPage = 'https://feheroes.gamepedia.com'

    if not os.path.isdir(heroFolder):
        os.mkdir(heroFolder)
    if not os.path.isdir(skillFolder):
        os.mkdir(skillFolder)

    # TODO: wrap the lists with classes 
    # that support easy searching without
    # having to know lambdas and list comprehension

    # default True : redownload all non hero files
    bReplaceNonHeroFiles = True
    # default False : do not redownload hero files   
    bReplaceHeroFiles = False       

    weaponList = []
    weaponfile = os.path.join(skillFolder, 'weapons.html')
    weaponURL = wikiPage + '/Weapons'

    upgradableList = []
    upgradableFile = os.path.join(skillFolder, 'upgradable.html')
    upgradableURL = wikiPage + "/List_of_upgradable_weapons"

    assistList = []
    assistFile = os.path.join(skillFolder, 'assists.html')
    assistURL = wikiPage + '/Assists'

    specialList = []
    specialFile = os.path.join(skillFolder, 'specials.html')
    specialURL = wikiPage + '/Specials'

    passiveList = []
    passiveFile = os.path.join(skillFolder, 'passives.html')
    passiveURL = wikiPage + '/Passives'

    heroList = []
    lvl40File = os.path.join(heroFolder, 'Level_40.html')
    lvl40URL = wikiPage + '/Level_40_stats_table'

    prfList = []
    prfFile = os.path.join(skillFolder, 'exclusive_skills.html')
    prfURL = wikiPage + '/Exclusive_skills'

    evolveFile = os.path.join(skillFolder, 'evolving_weapons.html')
    evolveURL = wikiPage + '/List_of_evolving_weapons'

    def curlFile(url, outfile, replace):
        if not replace:
            if os.path.isfile(outfile):
                print(outfile,"already exists")
                return
        with open(outfile, 'wb') as f:
            curl = pycurl.Curl()
            curl.setopt(pycurl.CAINFO, certifi.where())
            curl.setopt(pycurl.URL, url)
            curl.setopt(curl.WRITEDATA, f)
            curl.perform()
            curl.close()
            print("Curled", url, "to", outfile)


    def debugPrint(*argv):
        if debugMode:
            print(*argv)

    def curlSoup(url, outfile, replace):
        curlFile(url, outfile, replace)
        return BeautifulSoup(open(outfile,'rb'), 'html.parser')
    def urlStrip(inStr):
        return str(unidecode.unidecode(urllib.parse.unquote(inStr)))
    def tryStrToInt(intStr):
        if not intStr:
            warnings.warn("NoneType submitted to tryStrToInt", stacklevel=2)
            return 0
        if intStr.isnumeric():
            return int(intStr)
        else:
            return 0
    def getFlattenedString(node):
        if node.string != None:
            return urlStrip(node.string)
        res = ""
        for child in node.contents:
            res += getFlattenedString(child)
        return res


    # Gather list of weapons
    soup = curlSoup(weaponURL, weaponfile, bReplaceNonHeroFiles)
    pageTitle = soup.title.string.rsplit(" - Fire Emblem Heroes Wiki")[0]
    debugPrint(pageTitle)
    for n in soup.find_all("span", class_="mw-headline"):
        if (n.parent.name == "h2"):
            continue
        debugPrint("-"*70) 
        weaponType = n.string.rsplit("s",1)[0]
        if weaponType.startswith("Beast"):
            weaponType = "Beast"
        debugPrint("Weapon Type:", weaponType)
        debugPrint("-"*70) 
        weaponTable = n.parent.next_sibling.next_sibling.next_sibling.next_sibling
        for p in weaponTable.find_all("td", class_="field_Weapon"):
            weapon = Weapon()
            weapon.url = wikiPage + p.contents[0]['href']
            weapon.type = str(weaponType)
            weaponData = p.parent
            weapon.name = urlStrip(weaponData.find(class_="field_Weapon").contents[0]['title'])
            weapon.desc = getFlattenedString(weaponData.find(class_="field_Description"))
            weapon.mt = tryStrToInt(weaponData.find(class_="field_Might").string)
            weapon.range = tryStrToInt(weaponData.find(class_="field_Range").string)
            weapon.cost = tryStrToInt(weaponData.find(class_="field_SP").string)
            weapon.isPrf = ("Yes" == weaponData.find(class_="field_Exclusive").string)        
            weapon.isRefinable = False
            weapon.refines = []
            debugPrint(weapon.name)
            debugPrint("MT:", weapon.mt)
            debugPrint("Rng:", weapon.range)
            debugPrint("isPrf:", weapon.isPrf)
            debugPrint("SP:", weapon.cost)
            debugPrint(weapon.desc)
            debugPrint("-"*70)
            weaponList.append(weapon)


    # Gather list of refinable weapons
    soup = curlSoup(upgradableURL, upgradableFile, bReplaceNonHeroFiles)
    pageTitle = soup.title.string.rsplit(" - Fire Emblem Heroes Wiki")[0]
    debugPrint(pageTitle)
    for span in soup.find_all("span", class_="mw-headline"):
        if (span.parent.name == "h3"):
            debugPrint("-"*70)   
            weapType = span.string        
            debugPrint("Weapon Type:", weapType)
            debugPrint("-"*70)  
            weaponTable = span.parent.next_sibling.contents[0]
            # row 0 is used for table header
            currentRow = 1
            maxRow = weaponTable.contents.__len__()
            while (currentRow < maxRow):

                baseWeap = None
                baseWeapRow = weaponTable.contents[currentRow]
                baseEntry = baseWeapRow.contents[0]
                weapName = urlStrip(baseEntry.contents[0]['title'])
                numRefines = int(baseEntry['rowspan'])        

                for weap in weaponList:
                    if (weap.name == weapName):
                        baseWeap = weap
                        baseWeap.isRefinable = True
                        upgradableList.append(baseWeap)
                        continue

                currentRefineRow = baseWeapRow 
                refineEffectEntry = currentRefineRow.find_all(rowspan=True)[-2]
                refineEffectRange = int(refineEffectEntry['rowspan'])
                for i in range(numRefines):

                    currentRefine = Refine()
                    baseWeap.refines.append(currentRefine)
                    # fetch a new refinedEffect
                    if (refineEffectRange == 0):
                        refineEffectEntry = currentRefineRow.find_all(rowspan=True)[-1]
                        refineEffectRange = int(refineEffectEntry['rowspan'])
                    
                    refineEffectRange -= 1
                    currentRefine.desc = getFlattenedString(refineEffectEntry)
                    if ("(Unchanged)" == currentRefine.desc):
                        currentRefine.desc = str("(Unchanged) " + baseWeap.desc)
                    statRow = [node for node in currentRefineRow.contents if not "rowspan" in node.attrs][1:]
                    currentRefine.stats = list(map(getFlattenedString, statRow))
                    debugPrint("Refine: ")
                    # TODO: convert into array
                    debugPrint("Stat Changes:", " ".join(currentRefine.stats))
                    debugPrint("New Effect:", currentRefine.desc)
                    currentRefineRow = currentRefineRow.next_sibling
                # we have digested this many rows so advance the 
                # read index by that many
                currentRow += numRefines
                debugPrint("-"*70)


    # gather the assists
    soup = curlSoup(assistURL, assistFile, bReplaceNonHeroFiles)
    pageTitle = soup.title.string.rsplit(" - Fire Emblem Heroes Wiki")[0]
    debugPrint(pageTitle)

    assistTable = soup.find(string="Ardent Sacrifice").parent.parent.parent.parent
    for n in assistTable.find_all("a"):
        assist = Skill()
        assist.url = wikiPage + n['href']
        assist.slot = "Assist"
        assistData = n.parent.parent
        assist.name = getFlattenedString(assistData.find(class_="field_Name"))
        assist.desc = getFlattenedString(assistData.find(class_="field_Description"))
        assist.isPrf = ("cannot be inherited" in assist.desc)
        assist.cost = tryStrToInt(assistData.find(class_="field_SP").string)
        assist.range = tryStrToInt(assistData.find(class_="field_Range").string)
        assist.cd = 0
        debugPrint("-"*70)   
        debugPrint(assist.name)
        debugPrint("-"*70)
        debugPrint("isPrf:", assist.isPrf)
        debugPrint("SP:", assist.cost)
        debugPrint("Rng:", assist.range)       
        debugPrint(assist.desc)
        debugPrint("-"*70)
        assistList.append(assist)

    # gather the specials
    soup = curlSoup(specialURL, specialFile, bReplaceNonHeroFiles)
    pageTitle = soup.title.string.rsplit(" - Fire Emblem Heroes Wiki")[0]
    debugPrint(pageTitle)

    specialTable = soup.find(string="Aegis").parent.parent.parent.parent
    for n in specialTable.find_all("a"):
        special = Skill()
        special.url = wikiPage + n['href']
        special.slot = "Special"
        special.range = 0
        specialData = n.parent.parent
        special.name = getFlattenedString(specialData.find(class_="field_Name"))
        special.desc = getFlattenedString(specialData.find(class_="field_Description"))
        special.isPrf = ("cannot be inherited" in special.desc)
        special.cost = tryStrToInt(specialData.find(class_="field_SP").string)
        special.cd = tryStrToInt(specialData.find(class_="field_Cooldown").string)
        debugPrint("-"*70)   
        debugPrint(special.name)
        debugPrint("-"*70)
        debugPrint("isPrf:", special.isPrf)
        debugPrint("SP:", special.cost)
        debugPrint("CD:", special.cd)       
        debugPrint(special.desc)
        debugPrint("-"*70)
        specialList.append(special)


    # gather passives
    soup = curlSoup(passiveURL, passiveFile, bReplaceNonHeroFiles)
    pageTitle = soup.title.string.rsplit(" - Fire Emblem Heroes Wiki")[0]
    debugPrint(pageTitle)

    for n in soup.find_all("span",string=re.compile("^List of"), class_="mw-headline"):
        passiveType = n.string.split("List of ")[-1]
        debugPrint("-"*70) 
        debugPrint("PASSIVE TYPE:", passiveType)
        debugPrint("-"*70) 
        passiveTable = n.parent.next_sibling.next_sibling
        for p in passiveTable.find_all("a", title=True):
            passive = Skill()
            passive.url = wikiPage + p['href']
            passive.range = 0
            passive.cd = 0
            if ("Type" in passiveType):
                passive.slot = passiveType.split("Type ")[-1]
            else: 
                passive.slot = "Seal"
            passive.slot = str(passive.slot) # just in case
            passiveData = p.parent.parent
            passive.name = getFlattenedString(passiveData.find(class_="field_Name"))
            passive.desc = getFlattenedString(passiveData.find(class_="field_Description"))
            passive.cost = tryStrToInt(passiveData.find(class_="field_SP").string)
            passive.isPrf = ("Yes" == passiveData.find(class_="field_Is_exclusive").string)        
            debugPrint(passive.name)
            debugPrint("isPrf:", passive.isPrf)
            debugPrint("SP:", passive.cost)
            debugPrint(passive.desc)
            debugPrint("-"*70)
            passiveList.append(passive) 

    # process evolving weapons
    soup = curlSoup(evolveURL, evolveFile, bReplaceNonHeroFiles)
    evoTable = soup.find("a", href="/Armads").parent.parent.parent
    # first row is the table header
    for evoRow in evoTable.contents[1:]:
        origWeapName = urlStrip(evoRow.contents[1].contents[0]['title'])
        newWeapName = urlStrip(evoRow.contents[1].contents[-1]['title'])
        origWeap = [w for w in weaponList if w.name == origWeapName][0]
        newWeap = [w for w in weaponList if w.name == newWeapName][0]
        origWeap.evolutions.append(newWeap)

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
    # duoSkill          string
    # color             string
    # weapon            string
    # heroSrc           string
    # move              string
    # url
    def parseHero(soup, heroName, heroMod, heroURL):
        hero = Hero()
        heroList.append(hero)
        hero.name = urlStrip(heroName)
        hero.url = heroURL
        hero.mod = urlStrip(heroMod)
        hero.full_name = hero.name + ":" + hero.mod    

        for a in soup.find_all('a', string="Heroes", href=True):
            if a['href'] == "/Category:Heroes":
                for b in a.parent.parent.contents:
                    debugPrint("Category: ", b.string)    
                    hero.categories.append(str(b.string))
        
        hero.rarities = []
        rare_n = soup.find("span", string="Rarities").parent.next_sibling.next_sibling
        for r in rare_n.find_all("img"):
            rarity = int((r.previous_sibling.string)[-1:])
            debugPrint("Rarity: " + str(rarity))
            hero.rarities.append(rarity)
        time_n = soup.find("time")
        time = time_n.string
        hero.releaseDate = str(time)
        debugPrint("ReleaseDate: " + time)
        # stats blob

        pss = lambda x : list(map(tryStrToInt, x.split("/")))
        rss = lambda r : list(map(tryStrToInt, r.split("~")))

        stats_n = soup.find("span", string="Stats", class_="mw-headline")
        if (stats_n == None):
            stats_n = soup.find("span", string="Ally stats", class_="mw-headline")
        stats_n = stats_n.parent
        for sib in stats_n.next_siblings:
            if sib.string == "Level 1 stats":
                table_node = sib.next_sibling.contents[0]
                star = 1
                while (star <= 5):
                    debugPrint("★" * star , " lvl 1 stats: ")
                    rng_hp =  pss(table_node.contents[star].contents[1].string)
                    rng_atk = pss(table_node.contents[star].contents[2].string)
                    rng_spd = pss(table_node.contents[star].contents[3].string)
                    rng_def = pss(table_node.contents[star].contents[4].string)
                    rng_res = pss(table_node.contents[star].contents[5].string)
                    rng_totBB = rss(table_node.contents[star].contents[6].string)
                    neutralBST = rng_hp[1] + rng_atk[1] + rng_spd[1] + rng_def[1] + rng_res[1]
                    rng_tot = [rng_totBB[0], neutralBST, rng_totBB[-1]] 
                    debugPrint(rng_hp, rng_atk, rng_spd, rng_def, rng_res, rng_tot)
                    hero.lvl_1_Stats[star-1] = [rng_hp, rng_atk, rng_spd, rng_def, rng_res, rng_tot]                
                    star = star + 1            
                break    
        for sib2 in sib.next_siblings:
            if sib2.string == "Level 40 stats":
                table_node = sib2.next_sibling.contents[0]
                star = 1
                while (star <= 5):
                    debugPrint("★" * star , " lvl 40 stats: ")
                    rng_hp =  pss(table_node.contents[star].contents[1].string)
                    rng_atk = pss(table_node.contents[star].contents[2].string)
                    rng_spd = pss(table_node.contents[star].contents[3].string)
                    rng_def = pss(table_node.contents[star].contents[4].string)
                    rng_res = pss(table_node.contents[star].contents[5].string)
                    rng_totBB = rss(table_node.contents[star].contents[6].string)
                    neutralBST = rng_hp[1] + rng_atk[1] + rng_spd[1] + rng_def[1] + rng_res[1]
                    rng_tot = [rng_totBB[0], neutralBST, rng_totBB[-1]] 
                    debugPrint(rng_hp, rng_atk, rng_spd, rng_def, rng_res, rng_tot)
                    hero.lvl_40_Stats[star-1] = [rng_hp, rng_atk, rng_spd, rng_def, rng_res, rng_tot]                
                    star = star + 1
                break 

        # weap skills; hopefully assist/passives will be similar
        weap_n = soup.find("span", string="Weapons", class_="mw-headline")
        weap_n = weap_n.parent.next_sibling.next_sibling
        for w in weap_n.find_all("tr")[1:]:
            weap = w.find("a", class_ = None, href=True)
            weapName = urlStrip(weap['title'])
            weapData = weap.parent.next_sibling
            weapMight = tryStrToInt(weapData.string)
            weapData = weapData.next_sibling
            weapRange = tryStrToInt(weapData.string)
            weapData = weapData.next_sibling
            weapDesc = getFlattenedString(weapData)
            weapData = weapData.next_sibling
            weapSP = tryStrToInt(weapData.string)
            weapData = weapData.next_sibling
            weapDefaultStars = tryStrToInt(weapData.contents[0].string)
            weapData = weapData.next_sibling
            weapUnlockStars = tryStrToInt(weapData.contents[0].string)
            debugPrint(weapName, weapMight, weapRange, weapSP, "★" * weapDefaultStars, "★" * weapUnlockStars)
            debugPrint(weapDesc)

            for storedWeap in weaponList:
                if (storedWeap.name == weapName):
                    hero.weaponReqs.append([storedWeap, weapDefaultStars, weapUnlockStars, False])
                    break

        assist_n = soup.find("span", string="Assists", class_="mw-headline")
        assist_n = assist_n.parent.next_sibling.next_sibling
        for a in assist_n.find_all("tr")[1:]:
            assist = a.find("a", class_ = None, href=True)
            assistName = urlStrip(assist.string)
            assistData = assist.parent.next_sibling
            assistRange = assistData.string
            assistData = assistData.next_sibling
            assistDesc = getFlattenedString(assistData)
            assistData = assistData.next_sibling
            assistSP = assistData.string
            assistData = assistData.next_sibling
            assistDefaultStars = tryStrToInt(assistData.contents[0].string)
            assistData = assistData.next_sibling
            assistUnlockStars = tryStrToInt(assistData.contents[0].string)
            debugPrint(assistName, assistRange, assistSP, "★" * assistDefaultStars, "★" * assistUnlockStars)
            debugPrint(assistDesc)
            for storedAssist in assistList:
                if (storedAssist.name == assistName):
                    hero.skillReqs.append([storedAssist, assistDefaultStars, assistUnlockStars, False])
                    break        

        passive_n = soup.find("span", string="Passives", class_="mw-headline")
        passive_n = passive_n.parent.next_sibling.next_sibling
        for p in passive_n.find_all("tr")[1:]:
            passive = p.find("a", class_ = None, href=True)        
            passiveName = urlStrip(passive.string)
            passiveData = passive.parent
            passiveData = passiveData.next_sibling
            passiveDesc = getFlattenedString(passiveData)
            passiveData = passiveData.next_sibling
            passiveSP = passiveData.string
            passiveData = passiveData.next_sibling
            passiveUnlockStars = tryStrToInt(passiveData.contents[0].string)
            passiveData = passiveData.next_sibling
            debugPrint(passiveName, passiveSP, "★" * passiveUnlockStars)
            debugPrint(passiveDesc)
            for storedPassive in passiveList:
                if (storedPassive.name == passiveName):
                    hero.skillReqs.append([storedPassive, 0, passiveUnlockStars, False])
                    break           

        special_n = soup.find("span", string="Specials", class_="mw-headline")
        special_n = special_n.parent.next_sibling.next_sibling

        for s in special_n.find_all("tr")[1:]:
            special = s.find("a", class_ = None, href=True)        
            specialData = special.parent    
            specialName = urlStrip(special.string)        
            specialData = specialData.next_sibling
            specialCD = tryStrToInt(specialData.string)
            specialData = specialData.next_sibling
            specialDesc = getFlattenedString(specialData)
            specialData = specialData.next_sibling
            specialSP = tryStrToInt(specialData.string)
            specialData = specialData.next_sibling
            specialDefaultStars = tryStrToInt(specialData.contents[0].string)
            specialData = specialData.next_sibling
            specialUnlockStars = tryStrToInt(specialData.contents[0].string)
            debugPrint(specialName, specialCD, specialSP, "★" * specialDefaultStars, "★" * specialUnlockStars)
            debugPrint(specialDesc)
            for storedSpecial in specialList:
                if (storedSpecial.name == specialName):
                    hero.skillReqs.append([storedSpecial, specialDefaultStars, specialUnlockStars, False])
                    break    

        if hero.isDuo():
            hero.duoSkill = getFlattenedString(soup.find("a", string="Pair Up").parent)
        hero.finalize() 
    # end parseHero


    soup = curlSoup(lvl40URL, lvl40File, bReplaceNonHeroFiles)
    pageTitle = soup.title.string.rsplit(" - Fire Emblem Heroes Wiki")[0]
    debugPrint(pageTitle)   

    counter = 0
    for n in soup.find(class_="sortable wikitable", id="max-stats-table").contents[0].contents:
        m = n.find("a", href=True, title=True)
        if m != None:
            counter += 1
            heroURL = m['href']        
            (heroName, heroMod) = heroURL[1:].split(":")
            individualFolder = os.path.join(heroFolder, heroName)
            if not os.path.isdir(individualFolder):
                os.mkdir(individualFolder)
            heroPage = os.path.join(individualFolder, heroMod + ".html")
            heroSoup = curlSoup(wikiPage+heroURL, heroPage, bReplaceHeroFiles)
            parseHero(heroSoup, heroName, heroMod, wikiPage+heroURL)

    soup = curlSoup(prfURL, prfFile, bReplaceNonHeroFiles)
    pageTitle = soup.title.string.rsplit(" - Fire Emblem Heroes Wiki")[0]
    debugPrint(pageTitle)   

    # passives
    for prf_n in soup.find_all("td", class_ = "field_Name"):
        prfname = urlStrip(prf_n.contents[0]['title'])
        foundPassive = None
        for passive in passiveList:
            if (passive.name == prfname):
                foundPassive = passive
                break
        if foundPassive == None:
            # probably a new skill that hasnt been added to passives
            warnings.warn("Passive list does not contain " + prfname)
        else:
            foundPassive.isPrf = True

    # weapons
    for prf_n in soup.find_all("td", class_ = "field_Weapon"):
        prfname = urlStrip(prf_n.contents[0]['title'])
        foundWeap = None
        for weapon in weaponList:
            if (weapon.name == prfname):
                foundWeap = weapon
                break
        foundWeap.isPrf = True

    # specials
    for prf_n in soup.find_all("td", class_ = "field_Special"):
        prfname = urlStrip(prf_n.contents[0]['title'])
        foundSpecial = None
        for special in specialList:
            if (special.name == prfname):
                foundSpecial = special
                break
        foundSpecial.isPrf = True    

    # assists 
    for prf_n in soup.find_all("td", class_ = "field_Assist"):
        prfname = urlStrip(prf_n.contents[0]['title'])
        foundAssist = None
        for assist in assistList:
            if (assist.name == prfname):
                foundAssist = assist
                break
        foundAssist.isPrf = True   

    with open(pkl_output_file, 'wb') as f:
        p = pickle.Pickler(f)
        p.dump(weaponList)
        p.dump(upgradableList)
        p.dump(assistList)
        p.dump(specialList)
        p.dump(passiveList)
        p.dump(heroList)

    # sys.stdout.close()
