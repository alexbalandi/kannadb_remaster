import json
import os.path
import pickle
import re
import urllib.parse

from linus.feh.poro.poroparser_v2 import LoadPoro

from .poroAccents import accents

apiquery = "https://feheroes.gamepedia.com/api.php?"


def getHeroMFname(h):
    basename = h.name + " " + h.mod
    mfname = ""
    for c in basename:
        if c in accents:
            c = accents[c]
        mfname += c
    mfname = re.sub("[^A-Za-z _.0-9-]", "", mfname)
    # for now no resplendent
    mfname = "File:%s Face FC.webp" % mfname
    return mfname


def getIconURL(mfname):
    iconFields = {
        "action": "query",
        "format": "json",
        "titles": mfname,
        "prop": "imageinfo",
        "iiprop": "url",
    }
    cargoquery = apiquery + urllib.parse.urlencode(iconFields)
    curlJSON = json.loads(readURL(cargoquery))
    iconpage = list(curlJSON["query"]["pages"].values())[0]
    return iconpage["imageinfo"][0]["url"]


def readURL(url):
    url = urllib.request.urlopen(url)
    return url.read()


def BuildHeroPaths(pkl_output_file="porodb.pkl", pkl_paths_file="heropaths.pkl"):

    data = LoadPoro(pkl_output_file)
    data["skills"]
    heroes = data["heroes"]
    data["seals"]
    heropaths = {}
    for h in heroes:
        getHeroMFname(h)
    with open(pkl_paths_file, "wb") as f:
        p = pickle.Pickler(f)
        p.dump(heropaths)
    return data


def getIconPaths(pkl_icon_file="iconpaths.pkl"):
    with open(pkl_icon_file, "rb") as f:
        p = pickle.Unpickler(f)
        return p.load()


def getHeroPaths(pkl_paths_file="heropaths.pkl"):
    with open(pkl_paths_file, "rb") as f:
        p = pickle.Unpickler(f)
        return p.load()


def GetKannaURLs(pkl_output_file="porodb.pkl", pkl_paths_file="heropaths.pkl"):
    if not os.path.isfile(pkl_paths_file):
        return BuildHeroPaths(pkl_output_file, pkl_paths_file)
    data = LoadPoro(pkl_output_file)
    return data


def CurlKannaImages():
    data = GetKannaURLs()
    heroes = data["heroes"]
    msh = [h for h in heroes if "enemy" not in h.properties and h.iconURL is None]
    if len(msh) > 0:
        print(msh)
        print("Missing %d heroes" % len(msh))
    else:
        print("Got all heroes!")
    h = [h for h in heroes if h.name == "Linus"][0]
    print("Linus URL: %s" % h.iconURL)
