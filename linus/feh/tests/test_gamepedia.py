"""
Tests for all Gamepedia (feheroes.fandom.com) API interactions.

These tests mock urllib to avoid real network calls, ensuring the suite is
fast and deterministic. They cover the exact failure modes seen in
railway_failure.log (HTTP 403 due to missing User-Agent, missing pickle
files from failed curl) plus the full retry/error-handling contract.
"""

import urllib.error
import urllib.request
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from linus.feh.poro.porocurler_v2 import (
    getDuoHeroes,
    getHarmonizedHeroes,
    getLegendaryHeroes,
    getMythicHeroes,
    getRawDictFromTable,
    getRawDoubleDictFromTable,
    getRawEvolutions,
    getRawSeals,
    getRawSkills,
    getRawUnits,
    getRawUnitStats,
    getRawWeaponUpgrades,
    getSummonFocusUnits,
    getSummoningAvailability,
    readURL,
    verifyTableFields,
)

# ---------------------------------------------------------------------------
# XML fixtures
# ---------------------------------------------------------------------------

# Compact XML (no whitespace between tags) to match real Gamepedia API response format.
# BeautifulSoup's .contents includes NavigableString whitespace nodes when XML is indented,
# which causes AttributeError on .attrs — the real API returns compact XML without this issue.

CARGO_AUTOCOMPLETE_ALL = (
    b'<?xml version="1.0"?><api><cargoqueryautocomplete>'
    b'<p main_table="Skills"/><p main_table="Units"/><p main_table="UnitStats"/>'
    b'<p main_table="UnitSkills"/><p main_table="WeaponUpgrades"/>'
    b'<p main_table="WeaponEvolutions"/><p main_table="SacredSealCosts"/>'
    b'<p main_table="LegendaryHero"/><p main_table="DuoHero"/>'
    b'<p main_table="MythicHero"/><p main_table="HarmonizedHero"/>'
    b'<p main_table="SummoningEventFocuses"/><p main_table="SummoningAvailability"/>'
    b'<p main_table="Distributions"/>'
    b"</cargoqueryautocomplete></api>"
)

CARGO_AUTOCOMPLETE_SKILLS_FIELDS = (
    b'<?xml version="1.0"?><api><cargoqueryautocomplete>'
    b"<p>Skills.WikiName</p><p>Skills.Name</p><p>Skills.GroupName</p>"
    b"<p>Skills.Scategory</p><p>Skills.RefinePath</p><p>Skills.UseRange</p>"
    b"<p>Skills.Description</p><p>Skills.Required</p><p>Skills.Next</p>"
    b"<p>Skills.Exclusive</p><p>Skills.SP</p><p>Skills.CanUseMove</p>"
    b"<p>Skills.CanUseWeapon</p><p>Skills.Might</p><p>Skills.StatModifiers</p>"
    b"<p>Skills.Cooldown</p><p>Skills.Properties</p><p>Skills._pageName</p>"
    b"</cargoqueryautocomplete></api>"
)

CARGO_QUERY_SKILLS_PAGE1 = (
    b'<?xml version="1.0"?><api><cargoquery>'
    b'<row><field WikiName="Armorslayer" Name="Armorslayer" GroupName="Armorslayer"'
    b' Scategory="weapon" RefinePath="" UseRange="1"'
    b' Description="Effective against armored foes."'
    b' Required="" Next="Armorslayer+" Exclusive="" SP="200"'
    b' CanUseMove="Infantry,Cavalry,Armored,Flying" CanUseWeapon="Red Sword"'
    b' Might="8" StatModifiers="" Cooldown="" Properties="" Page="Armorslayer"/></row>'
    b"</cargoquery></api>"
)

CARGO_QUERY_EMPTY = b'<?xml version="1.0"?><api><cargoquery></cargoquery></api>'

API_ERROR_FORBIDDEN = (
    b'<?xml version="1.0"?><api>'
    b'<error code="readapidenied" info="You need read permission to use this module."/>'
    b"</api>"
)

API_ERROR_RATE_LIMITED = (
    b'<?xml version="1.0"?><api>' b'<error code="ratelimited" info="You have exceeded your rate limit."/>' b"</api>"
)


def _make_response(content: bytes, status: int = 200):
    """Build a mock urllib response object."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = content
    mock_resp.status = status
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _http_error(code: int, reason: str = "Error") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="https://example.com",
        code=code,
        msg=reason,
        hdrs={},
        fp=BytesIO(b""),
    )


# ---------------------------------------------------------------------------
# readURL: User-Agent header (the railway_failure.log root cause)
# ---------------------------------------------------------------------------


class TestReadURLUserAgent:
    """The root cause of the railway failure was a missing User-Agent header.
    Gamepedia/Fandom returns HTTP 403 to requests without one."""

    def test_sends_user_agent_header(self):
        """readURL must attach a User-Agent so Fandom doesn't 403 us."""
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = _make_response(b"data")
            readURL("https://feheroes.gamepedia.com/api.php?action=test")

        assert mock_open.called
        request_arg = mock_open.call_args[0][0]
        assert isinstance(request_arg, urllib.request.Request)
        # urllib.request.Request normalizes header keys to title-case ("User-agent")
        headers_lower = {k.lower(): v for k, v in request_arg.headers.items()}
        assert "user-agent" in headers_lower
        assert headers_lower["user-agent"] != ""

    def test_returns_content_on_200(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = _make_response(b"hello world")
            result = readURL("https://example.com")
        assert result == b"hello world"

    def test_raises_immediately_on_403(self):
        """HTTP 403 must NOT be retried — it's an auth/block issue, retrying won't help."""
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = _http_error(403, "Forbidden")
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                readURL("https://example.com", max_retries=3)
        assert exc_info.value.code == 403
        # Must not have retried: only 1 attempt
        assert mock_open.call_count == 1

    def test_raises_immediately_on_404(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = _http_error(404, "Not Found")
            with pytest.raises(urllib.error.HTTPError):
                readURL("https://example.com", max_retries=3)
        assert mock_open.call_count == 1

    def test_retries_on_429_rate_limit(self):
        """HTTP 429 Too Many Requests must be retried with a delay."""
        with patch("urllib.request.urlopen") as mock_open, patch("time.sleep") as mock_sleep:
            mock_open.side_effect = [
                _http_error(429, "Too Many Requests"),
                _make_response(b"ok"),
            ]
            result = readURL("https://example.com", max_retries=3, rate_limit_delay=1)
        assert result == b"ok"
        assert mock_open.call_count == 2
        mock_sleep.assert_called_once_with(1)

    def test_retries_on_500_server_error(self):
        """5xx errors are transient — must be retried with exponential backoff."""
        with patch("urllib.request.urlopen") as mock_open, patch("time.sleep"):
            mock_open.side_effect = [
                _http_error(503, "Service Unavailable"),
                _make_response(b"ok"),
            ]
            result = readURL("https://example.com", max_retries=3, initial_delay=1)
        assert result == b"ok"
        assert mock_open.call_count == 2

    def test_raises_after_max_retries_on_500(self):
        with patch("urllib.request.urlopen") as mock_open, patch("time.sleep"):
            mock_open.side_effect = _http_error(500, "Internal Server Error")
            with pytest.raises(urllib.error.HTTPError):
                readURL("https://example.com", max_retries=3, initial_delay=1)
        assert mock_open.call_count == 3

    def test_retries_on_network_error(self):
        with patch("urllib.request.urlopen") as mock_open, patch("time.sleep"):
            mock_open.side_effect = [OSError("connection reset"), _make_response(b"ok")]
            result = readURL("https://example.com", max_retries=3, initial_delay=1)
        assert result == b"ok"

    def test_raises_connection_error_after_all_network_retries(self):
        with patch("urllib.request.urlopen") as mock_open, patch("time.sleep"):
            mock_open.side_effect = OSError("no route to host")
            with pytest.raises((OSError, ConnectionError)):
                readURL("https://example.com", max_retries=2, initial_delay=1)

    def test_detects_api_level_rate_limit_in_xml_body(self):
        """Gamepedia sometimes returns 200 with a ratelimited error in the XML body."""
        with patch("urllib.request.urlopen") as mock_open, patch("time.sleep"):
            mock_open.side_effect = [
                _make_response(API_ERROR_RATE_LIMITED),
                _make_response(b"<?xml version='1.0'?><api><cargoquery/></api>"),
            ]
            readURL("https://example.com", max_retries=3, rate_limit_delay=1)
        # Should have retried after detecting rate limit in XML
        assert mock_open.call_count == 2


# ---------------------------------------------------------------------------
# verifyTableFields
# ---------------------------------------------------------------------------


def _patch_read_url_soup(responses):
    """Helper: patch readURLSoup to return BeautifulSoup objects from XML bytes."""
    from bs4 import BeautifulSoup

    soups = [BeautifulSoup(r, "lxml-xml") for r in responses]
    return patch("linus.feh.poro.porocurler_v2.readURLSoup", side_effect=soups)


class TestVerifyTableFields:
    def test_passes_for_valid_table_and_fields(self):
        with _patch_read_url_soup([CARGO_AUTOCOMPLETE_ALL, CARGO_AUTOCOMPLETE_SKILLS_FIELDS]), patch("time.sleep"):
            # Should not raise
            verifyTableFields("Skills", ["_pageName=Page", "WikiName", "Name"])

    def test_raises_when_table_not_in_wiki(self):
        with _patch_read_url_soup([CARGO_AUTOCOMPLETE_ALL, CARGO_AUTOCOMPLETE_SKILLS_FIELDS]), patch("time.sleep"):
            with pytest.raises(ValueError):
                verifyTableFields("NonExistentTable", ["SomeField"])

    def test_raises_when_field_not_in_table(self):
        with _patch_read_url_soup([CARGO_AUTOCOMPLETE_ALL, CARGO_AUTOCOMPLETE_SKILLS_FIELDS]), patch("time.sleep"):
            with pytest.raises(ValueError):
                verifyTableFields("Skills", ["NonExistentField"])

    def test_skips_row_id_field(self):
        """_rowID is a virtual field and should not be validated against the schema."""
        with _patch_read_url_soup([CARGO_AUTOCOMPLETE_ALL, CARGO_AUTOCOMPLETE_SKILLS_FIELDS]), patch("time.sleep"):
            # _rowID=ID alias should not trigger a field-not-found error
            verifyTableFields("Skills", ["_rowID=ID", "WikiName"])

    def test_raises_on_api_error_response(self):
        from bs4 import BeautifulSoup

        error_soup = BeautifulSoup(API_ERROR_FORBIDDEN, "lxml-xml")
        with patch("linus.feh.poro.porocurler_v2.readURLSoup", return_value=error_soup):
            with pytest.raises(ValueError, match="API Error"):
                verifyTableFields("Skills", ["WikiName"])


# ---------------------------------------------------------------------------
# getRawDictFromTable
# ---------------------------------------------------------------------------


class TestGetRawDictFromTable:
    def _autocomplete_responses(self, table="Skills", field_xml=None):
        return [
            CARGO_AUTOCOMPLETE_ALL,
            field_xml or CARGO_AUTOCOMPLETE_SKILLS_FIELDS,
        ]

    def test_returns_dict_keyed_by_base_field(self):
        responses = self._autocomplete_responses() + [CARGO_QUERY_SKILLS_PAGE1, CARGO_QUERY_EMPTY]
        with _patch_read_url_soup(responses), patch("time.sleep"):
            result = getRawDictFromTable("Skills", ["_pageName=Page", "WikiName", "Name"], "WikiName")
        assert "Armorslayer" in result
        assert result["Armorslayer"]["Name"] == "Armorslayer"

    def test_paginates_until_empty(self):
        """Should keep fetching pages until an empty result is returned."""
        page1 = CARGO_QUERY_SKILLS_PAGE1
        # Build a second page with a different entry
        page2 = (
            b'<?xml version="1.0"?><api><cargoquery>'
            b'<row><field WikiName="Iron Sword" Name="Iron Sword" GroupName="Iron Sword"'
            b' Scategory="weapon" RefinePath="" UseRange="1" Description="A basic sword."'
            b' Required="" Next="Steel Sword" Exclusive="" SP="50"'
            b' CanUseMove="Infantry,Cavalry,Armored,Flying" CanUseWeapon="Red Sword"'
            b' Might="6" StatModifiers="" Cooldown="" Properties="" Page="Iron Sword"/></row>'
            b"</cargoquery></api>"
        )
        empty = CARGO_QUERY_EMPTY
        responses = self._autocomplete_responses() + [page1, page2, empty]
        with _patch_read_url_soup(responses), patch("time.sleep"):
            result = getRawDictFromTable("Skills", ["_pageName=Page", "WikiName", "Name"], "WikiName")
        assert "Armorslayer" in result
        assert "Iron Sword" in result

    def test_raises_when_base_field_not_in_fields_list(self):
        with pytest.raises(ValueError):
            getRawDictFromTable("Skills", ["WikiName", "Name"], "NonExistentKey")

    def test_warns_on_duplicate_entry(self):
        dupe = (
            b'<?xml version="1.0"?><api><cargoquery>'
            b'<row><field WikiName="Armorslayer" Name="Armorslayer" GroupName="" Scategory="weapon"'
            b' RefinePath="" UseRange="1" Description="" Required="" Next="" Exclusive=""'
            b' SP="200" CanUseMove="" CanUseWeapon="" Might="8" StatModifiers=""'
            b' Cooldown="" Properties="" Page="Armorslayer"/></row>'
            b'<row><field WikiName="Armorslayer" Name="Armorslayer+" GroupName="" Scategory="weapon"'
            b' RefinePath="" UseRange="1" Description="" Required="" Next="" Exclusive=""'
            b' SP="300" CanUseMove="" CanUseWeapon="" Might="10" StatModifiers=""'
            b' Cooldown="" Properties="" Page="Armorslayer+"/></row>'
            b"</cargoquery></api>"
        )
        responses = self._autocomplete_responses() + [dupe, CARGO_QUERY_EMPTY]
        import warnings as _warnings

        with _patch_read_url_soup(responses), patch("time.sleep"):
            with _warnings.catch_warnings(record=True) as caught:
                _warnings.simplefilter("always")
                getRawDictFromTable("Skills", ["_pageName=Page", "WikiName", "Name"], "WikiName")
        assert any("duplicate" in str(w.message).lower() for w in caught)

    def test_raises_on_api_error_in_cargoquery(self):
        from bs4 import BeautifulSoup

        autocomplete_soup1 = BeautifulSoup(CARGO_AUTOCOMPLETE_ALL, "lxml-xml")
        autocomplete_soup2 = BeautifulSoup(CARGO_AUTOCOMPLETE_SKILLS_FIELDS, "lxml-xml")
        error_soup = BeautifulSoup(API_ERROR_FORBIDDEN, "lxml-xml")
        with patch(
            "linus.feh.poro.porocurler_v2.readURLSoup", side_effect=[autocomplete_soup1, autocomplete_soup2, error_soup]
        ), patch("time.sleep"):
            with pytest.raises(ValueError, match="API Error"):
                getRawDictFromTable("Skills", ["_pageName=Page", "WikiName", "Name"], "WikiName")


# ---------------------------------------------------------------------------
# Helper to build compact field-list XML (must be defined before module-level
# fixtures that call it below)
# ---------------------------------------------------------------------------


def _fields_xml(table: str, fields: list[str]) -> bytes:
    """Build a compact cargoqueryautocomplete fields response."""
    inner = "".join(f"<p>{table}.{f}</p>" for f in fields)
    return f'<?xml version="1.0"?><api><cargoqueryautocomplete>{inner}</cargoqueryautocomplete></api>'.encode()


# ---------------------------------------------------------------------------
# getRawDoubleDictFromTable
# ---------------------------------------------------------------------------

CARGO_AUTOCOMPLETE_UNITSKILLS_FIELDS = _fields_xml(
    "UnitSkills", ["WikiName", "skill", "skillPos", "defaultRarity", "unlockRarity"]
)

CARGO_QUERY_UNITSKILLS = (
    b'<?xml version="1.0"?><api><cargoquery>'
    b'<row><field WikiName="Linus" skill="Basilikos" skillPos="0" defaultRarity="5" unlockRarity="5"/></row>'
    b'<row><field WikiName="Linus" skill="Death Blow 3" skillPos="1" defaultRarity="5" unlockRarity="5"/></row>'
    b'<row><field WikiName="Hector" skill="Armads" skillPos="0" defaultRarity="5" unlockRarity="5"/></row>'
    b"</cargoquery></api>"
)


class TestGetRawDoubleDictFromTable:
    def test_returns_nested_dict(self):
        responses = [
            CARGO_AUTOCOMPLETE_ALL,
            CARGO_AUTOCOMPLETE_UNITSKILLS_FIELDS,
            CARGO_QUERY_UNITSKILLS,
            CARGO_QUERY_EMPTY,
        ]
        with _patch_read_url_soup(responses), patch("time.sleep"):
            result = getRawDoubleDictFromTable(
                "UnitSkills", ["WikiName", "skill", "skillPos", "defaultRarity", "unlockRarity"], "WikiName", "skill"
            )
        assert "Linus" in result
        assert "Basilikos" in result["Linus"]
        assert "Hector" in result
        assert "Armads" in result["Hector"]

    def test_raises_when_secondary_field_not_in_list(self):
        with pytest.raises(ValueError):
            getRawDoubleDictFromTable("UnitSkills", ["WikiName", "skill"], "WikiName", "NoField")


# ---------------------------------------------------------------------------
# High-level table fetchers: correct table names and key fields
# ---------------------------------------------------------------------------


AUTOCOMPLETE_UNITS_FIELDS = _fields_xml(
    "Units",
    [
        "_pageID",
        "_pageName",
        "Name",
        "Title",
        "WikiName",
        "Person",
        "Origin",
        "IntID",
        "Gender",
        "WeaponType",
        "MoveType",
        "GrowthMod",
        "Artist",
        "AdditionDate",
        "ReleaseDate",
        "Properties",
        "Description",
    ],
)
AUTOCOMPLETE_UNITSTATS_FIELDS = _fields_xml(
    "UnitStats",
    ["WikiName", "Lv1HP5", "Lv1Atk5", "Lv1Spd5", "Lv1Def5", "Lv1Res5", "HPGR3", "AtkGR3", "SpdGR3", "DefGR3", "ResGR3"],
)
AUTOCOMPLETE_UPGRADES_FIELDS = _fields_xml(
    "WeaponUpgrades",
    ["BaseWeapon", "UpgradesInto", "CostMedals", "CostStones", "CostDews", "StatModifiers", "BaseDesc", "AddedDesc"],
)
AUTOCOMPLETE_EVOLUTIONS_FIELDS = _fields_xml(
    "WeaponEvolutions", ["BaseWeapon", "EvolvesInto", "CostMedals", "CostStones", "CostDew"]
)
AUTOCOMPLETE_SEALS_FIELDS = _fields_xml(
    "SacredSealCosts", ["Skill", "BadgeColor", "BadgeCost", "GreatBadgeCost", "SacredCoinCost"]
)
AUTOCOMPLETE_LEG_FIELDS = _fields_xml("LegendaryHero", ["_pageName", "LegendaryEffect", "Duel"])
AUTOCOMPLETE_DUO_FIELDS = _fields_xml(
    "DuoHero", ["_pageName", "DuoSkill", "WikiSecondPerson", "WikiThirdPerson", "Duel"]
)
AUTOCOMPLETE_MYTHIC_FIELDS = _fields_xml("MythicHero", ["_pageName", "MythicEffect"])
AUTOCOMPLETE_HARMONIZED_FIELDS = _fields_xml(
    "HarmonizedHero", ["_pageName", "HarmonizedSkill", "WikiSecondPerson", "WikiThirdPerson"]
)
AUTOCOMPLETE_SUMMON_FOCUSES_FIELDS = _fields_xml("SummoningEventFocuses", ["_rowID", "WikiName", "Unit", "Rarity"])
AUTOCOMPLETE_SUMMONING_AVAIL_FIELDS = _fields_xml(
    "SummoningAvailability", ["_rowID", "_pageName", "Rarity", "StartTime", "EndTime"]
)


def _mock_fetcher(table_fields_xml, row_attrs, base_key):
    """Patch readURLSoup and return a single-row result for a high-level fetcher test."""
    from bs4 import BeautifulSoup

    row_xml = f'<?xml version="1.0"?><api><cargoquery><row><field {row_attrs}/></row></cargoquery></api>'.encode()
    soups = [
        BeautifulSoup(CARGO_AUTOCOMPLETE_ALL, "lxml-xml"),
        BeautifulSoup(table_fields_xml, "lxml-xml"),
        BeautifulSoup(row_xml, "lxml-xml"),
        BeautifulSoup(CARGO_QUERY_EMPTY, "lxml-xml"),
    ]
    return patch("linus.feh.poro.porocurler_v2.readURLSoup", side_effect=soups)


class TestHighLevelFetchers:
    """Smoke-test each high-level fetcher: correct table, correct key field, returns dict."""

    def test_getRawSkills(self):
        attrs = (
            'WikiName="Armorslayer" Name="Armorslayer" GroupName="Armorslayer" '
            'Scategory="weapon" RefinePath="" UseRange="1" Description="desc" '
            'Required="" Next="" Exclusive="" SP="200" CanUseMove="" '
            'CanUseWeapon="Red Sword" Might="8" StatModifiers="" Cooldown="" '
            'Properties="" Page="Armorslayer"'
        )
        with _mock_fetcher(CARGO_AUTOCOMPLETE_SKILLS_FIELDS, attrs, "WikiName"), patch("time.sleep"):
            result = getRawSkills()
        assert "Armorslayer" in result

    def test_getRawUnits(self):
        attrs = (
            'WikiName="Linus" Name="Linus" Title="Mad Dog" Person="Linus" '
            'Origin="Fire Emblem: The Blazing Blade" IntID="42" Gender="Male" '
            'WeaponType="Green Axe" MoveType="Infantry" GrowthMod="" Artist="" '
            'AdditionDate="2017-05-01" ReleaseDate="2017-05-01" Properties="" '
            'Description="desc" PageID="1" Page="Linus"'
        )
        with _mock_fetcher(AUTOCOMPLETE_UNITS_FIELDS, attrs, "WikiName"), patch("time.sleep"):
            result = getRawUnits()
        assert "Linus" in result

    def test_getRawUnitStats(self):
        attrs = (
            'WikiName="Linus" Lv1HP5="18" Lv1Atk5="10" Lv1Spd5="7" '
            'Lv1Def5="7" Lv1Res5="4" HPGR3="70" AtkGR3="65" SpdGR3="60" '
            'DefGR3="55" ResGR3="50"'
        )
        with _mock_fetcher(AUTOCOMPLETE_UNITSTATS_FIELDS, attrs, "WikiName"), patch("time.sleep"):
            result = getRawUnitStats()
        assert "Linus" in result
        assert result["Linus"]["Lv1HP5"] == "18"

    def test_getRawWeaponUpgrades(self):
        attrs = (
            'UpgradesInto="Basilikos+" BaseWeapon="Basilikos" CostMedals="50" '
            'CostStones="10" CostDews="0" StatModifiers="" BaseDesc="" AddedDesc=""'
        )
        with _mock_fetcher(AUTOCOMPLETE_UPGRADES_FIELDS, attrs, "UpgradesInto"), patch("time.sleep"):
            result = getRawWeaponUpgrades()
        assert "Basilikos+" in result

    def test_getRawSeals(self):
        attrs = 'Skill="Atk Smoke 1" BadgeColor="red" BadgeCost="20" ' 'GreatBadgeCost="5" SacredCoinCost="30"'
        with _mock_fetcher(AUTOCOMPLETE_SEALS_FIELDS, attrs, "Skill"), patch("time.sleep"):
            result = getRawSeals()
        assert "Atk Smoke 1" in result

    def test_getLegendaryHeroes(self):
        attrs = 'Page="Legendary Lyn" LegendaryEffect="Wind" Duel="170"'
        with _mock_fetcher(AUTOCOMPLETE_LEG_FIELDS, attrs, "Page"), patch("time.sleep"):
            result = getLegendaryHeroes()
        assert "Legendary Lyn" in result
        assert result["Legendary Lyn"]["LegendaryEffect"] == "Wind"

    def test_getDuoHeroes(self):
        attrs = (
            'Page="Ephraim &amp; Myrrh" DuoSkill="Duo of Twins" '
            'WikiSecondPerson="Myrrh" WikiThirdPerson="" Duel="160"'
        )
        with _mock_fetcher(AUTOCOMPLETE_DUO_FIELDS, attrs, "Page"), patch("time.sleep"):
            result = getDuoHeroes()
        assert "Ephraim & Myrrh" in result

    def test_getMythicHeroes(self):
        attrs = 'Page="Legendary Hector" MythicEffect="Anima"'
        with _mock_fetcher(AUTOCOMPLETE_MYTHIC_FIELDS, attrs, "Page"), patch("time.sleep"):
            result = getMythicHeroes()
        assert "Legendary Hector" in result
        assert result["Legendary Hector"]["MythicEffect"] == "Anima"

    def test_getHarmonizedHeroes(self):
        attrs = 'Page="Hríd &amp; Nifl" HarmonizedSkill="Sibling Harmony" ' 'WikiSecondPerson="Nifl" WikiThirdPerson=""'
        with _mock_fetcher(AUTOCOMPLETE_HARMONIZED_FIELDS, attrs, "Page"), patch("time.sleep"):
            result = getHarmonizedHeroes()
        assert "Hríd & Nifl" in result

    def test_getSummonFocusUnits(self):
        attrs = 'ID="1" WikiName="Linus" Unit="Linus" Rarity="5"'
        with _mock_fetcher(AUTOCOMPLETE_SUMMON_FOCUSES_FIELDS, attrs, "ID"), patch("time.sleep"):
            result = getSummonFocusUnits()
        assert "1" in result

    def test_getSummoningAvailability(self):
        attrs = 'ID="1" Page="Hero Fest" Rarity="5" ' 'StartTime="2017-05-01 00:00:00" EndTime="2017-05-14 23:59:59"'
        with _mock_fetcher(AUTOCOMPLETE_SUMMONING_AVAIL_FIELDS, attrs, "ID"), patch("time.sleep"):
            result = getSummoningAvailability()
        assert "1" in result


# ---------------------------------------------------------------------------
# getRawEvolutions (uses getRawDoubleDictFromTable)
# ---------------------------------------------------------------------------


class TestGetRawEvolutions:
    def test_returns_double_dict(self):
        from bs4 import BeautifulSoup

        row_xml = (
            b'<?xml version="1.0"?><api><cargoquery>'
            b'<row><field BaseWeapon="Basilikos" EvolvesInto="Basilikos (Refined)"'
            b' CostMedals="50" CostStones="10" CostDew="0"/></row>'
            b"</cargoquery></api>"
        )
        soups = [
            BeautifulSoup(CARGO_AUTOCOMPLETE_ALL, "lxml-xml"),
            BeautifulSoup(AUTOCOMPLETE_EVOLUTIONS_FIELDS, "lxml-xml"),
            BeautifulSoup(row_xml, "lxml-xml"),
            BeautifulSoup(CARGO_QUERY_EMPTY, "lxml-xml"),
        ]
        with patch("linus.feh.poro.porocurler_v2.readURLSoup", side_effect=soups), patch("time.sleep"):
            result = getRawEvolutions()
        assert "Basilikos" in result
        assert "Basilikos (Refined)" in result["Basilikos"]


# ---------------------------------------------------------------------------
# poroimagecurler.readURL: also needs User-Agent (secondary bug)
# ---------------------------------------------------------------------------


class TestImageCurlerReadURL:
    def test_sends_user_agent_header(self):
        from linus.feh.poro import poroimagecurler

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = _make_response(b'{"query":{"pages":{}}}')
            poroimagecurler.readURL("https://feheroes.gamepedia.com/api.php?action=query")

        request_arg = mock_open.call_args[0][0]
        assert isinstance(request_arg, urllib.request.Request)
        # urllib.request.Request normalizes header keys to title-case ("User-agent")
        headers_lower = {k.lower(): v for k, v in request_arg.headers.items()}
        assert "user-agent" in headers_lower
        assert headers_lower["user-agent"] != ""

    def test_uses_ssl_context(self):
        from linus.feh.poro import poroimagecurler

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = _make_response(b"data")
            poroimagecurler.readURL("https://example.com")

        # Keyword arg 'context' should be an ssl.SSLContext
        import ssl

        _, kwargs = mock_open.call_args
        assert "context" in kwargs
        assert isinstance(kwargs["context"], ssl.SSLContext)
