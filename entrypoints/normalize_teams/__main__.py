import csv
import pathlib
import re

import bracket_util
import club_util

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_SIMPLE_NAME = re.compile(r"^[a-z0-9 ]+$")
_FALSE_DUPLICATE_CARDINAL = frozenset(
    ["Cardinals Wrestling Club", "Arlington Cardinals Wrestling Club"]
)
# TODO: Deal with team names that have no match
# 1006
# 1006 legacy elite
# 1006 Legacy Elite
# Aces
# Aj Jr Wildcats Wrestling
# Alber Athletics
# Alber Athletics- WI
# Alton Little Redbirds
# Alton Little RedBirds
# Alton Little Redbirds Wrestlin
# Antioch Predators
# Antioch Predators Wrestling Cl
# Argenta Oreana Kids Wrestling
# Argenta-Oreana Kids Wrestling
# Arlington Cardinals
# Arlington Cardinals Wrestling
# Askren Wrestling Academy
# Assumption Elite
# B.A.M. Training Center
# Backyard Brawlers Midwest
# Backyard Brawlers North
# Backyard Brawlers North Wrestl
# Badger
# Badgers
# BAM
# Barrington Broncos Wrestling C
# Batavia Wrestling
# Beat The Streets - Avondale
# beat the streets avondale
# Beat The Streets Chicago- Avon
# Beat the Streets Chicago-Midwa
# Beat the Streets Chicago-Oak P
# Beat the Streets Midway
# Beat the Streets Oak Park
# Beat the streets Roseland
# Beat the Streets- Roseland
# Belleville Little Devils
# Belleville Little Devils Wrest
# Belvedere Bandits WC
# Belvidere Bandits
# Belvidere Bandits Wrestling Cl
# Bethalto Bulls
# Big Game Wrestling Club
# Bismarck Henning Wrestling Clu
# Bismarck-Henning Wrestling Clu
# Bismarck-Henning Youth Wrestling
# BJR
# Bloomingdale Bears
# Blue Line Training Academy
# Bolingbrook girls wrestling
# Bolingbrook girls wrestling cl
# Bolingbrook Jr Raiders
# Bolingbrook Junior Raiders
# Bolingbrook Junior Raiders Wre
# Brawlers
# Brawlers Wrestling
# Brodhead Wrestling Club
# BTS - Avondale
# BTS - Midway
# BTS - Tri Taylor
# BTS Avondale
# BTS Chicago Midway
# BTS Midway
# BTS Oak Park
# BTS Roseland
# BTS Tri Taylor
# BTS- Oak Park
# BTS- Roseland
# BTS-Avondale
# BTS-Midway
# BTS-Oak Park
# BTS-Roseland
# BTS-ROSELAND
# BTS-Tri Taylor
# BTSC - Avondale
# BTSC-Roseland
# Built by Brunson
# Built By Brunson
# Bulldog Elite
# Bulldog WC (Indiana)
# Bulldog Wrestling
# Bulldog Wrestling (Indiana)
# Bulldog Wrestling Club
# Bulldog Wrestling Club (Indiana)
# Bulls
# Callan
# Callan Wrestling
# Cape Central Wrestling Club
# Caravan
# Caravan Kid WC
# Caravan Kids
# Carbondale
# Castle Wrestling Club
# Celtics Wrestling Academy
# Centralia Jr. Orphans
# CHAMPIONS
# Charleston Kids Club Wrestling
# Chatham Wresling Club
# Chesterton WC (Indiana)
# Chesterton Wrestling Club
# Choose Hard Wrestling Academy (Indiana)
# CICC
# Clippers
# Club Madison Wrestling
# Combative sports
# Combative Sports
# Combative Sports Athletic Cent
# Contenders Wrestling Academy
# Cory Clark
# Cory Clark WC (West Chicago)
# Crosstown Spartan Elite
# Crosstown Spartan Elite Wrestl
# Crown point
# Crown Point Wrestling Club
# Crystal lake wizards
# Crystal Lake wizards
# Crystal Lake Wizards
# Crystal Lake Wizards Wrestling
# Cumberland youth wrestling
# Cumberland Youth Wrestling
# Cumberland Youth Wrestling Clu
# CWC
# Dakota
# DC Bolts
# DC Wrestling
# Decatur Dawgs
# Decatur Dawgs Wrestling
# Delavan-Darien
# Demolition
# DEMOLITION
# Demolition (South Chicago)
# Demoliton WC
# Demons WC (Burlington)
# Dinamo
# Doom
# DOOM
# Dubuque Wrestling Club
# Dundee highlanders
# Dundee Highlanders
# DuPec
# DuPec Wrestling Club
# Dupo QB
# Dupo Quarterback Club
# Dupo Quarterback wrestling clu
# Dwight
# East Peoria River Bandits
# East Peoria River Bandits WC
# East Peoria River Bandits Wres
# East Saint Louis Wrestling Club
# Edgemont Warriors
# Effingham Youth Wrestling
# El Paso Gridley Youth Wrestlin
# El Paso Gridley Youth Wrestlng
# El Paso Gridley YWC
# El Paso Wrestling Club
# Elite Athletic Club (Indiana)
# Elite Wrestling Academy
# Elk Grove Jr Grens
# Elk Grove Jr. Grens
# Elk Grove Junior Grens
# Elmhurst Titans
# Elmhurst Titans Wrestling Acad
# Englewood Live Wire
# EWC
# FCA Force
# FCA FORCE
# FH Jr Vikings
# FH Jr Vikings Wrestling Club
# FH Jr. Vikings
# FH Junior Vikings
# FH JUNIOR VIKINGS
# FH Spartans
# Fighting Farmers
# Force Elite
# Force Elite (South Chicago)
# Force Elite Wrestling
# Fort Zumwalt Wrestling
# Fox Wrestling Club
# Frankfort Gladiator Wresting
# Frankfort Gladiators
# Frankfort Gladiators WC
# Frankfort wildcats
# Frankfort Wildcats
# Franklin Central Wrestling Club
# Fraser WC
# GE Jr Rams
# Geneva Junior Vikings
# Geneva Junior Vikings Wrestling
# GGT wrestling
# Glenbard East Jr Rams
# Glenbard East Jr. Rams
# Glendale
# Golden
# Golden Eagles
# Golden Eagles Wrestling
# Gomez wrestling
# Grassfield Grizzlies
# Grayling Youth WC
# Grayslake WC
# Grayslake Wrestling Club
# Hannibal Pirates YC
# Harvey Twisters
# HARVEY TWISTERS
# Hawks Wrestling Club
# Headlock
# HEADLOCK
# Headlock Wrestling
# Herrin Tigers
# HF-RTC
# HFRTC
# Highland Bulldog Jr. Wrestling
# HIGHLAND BULLDOGS
# Highland Bulldogs Jr
# Highland Wrestling Club
# Hillsboro Jr Toppers
# Hillsboro Jr Toppers Wrestling
# Hillsboro Jr. Toppers
# Hillsboro wrestling club
# Honenegah
# Hoopeston Area WC
# Iguana Athletics Wrestling Clu
# Iguana WC
# iguana wrestling club
# Iguana Wrestling Club
# Iguanas WC
# Iguanas Wrestling Club
# Illini Bluffs Kids Wrestling
# Illini Bluffs Kids Wrestling C
# Impact wrestling academy
# Impact Wrestling Academy
# Irish wrestling
# Irish Wrestling
# Ironmen Wrestling Academy
# Jackson USA Wrestling
# Jackson USA Wrestling Club
# Jackson WC
# Jackson Wrestling Club
# Jake Reicin Wrestling Club
# Jersey Junior Panthers Wrestli
# Jerseyville Junior Panthers
# Jr Bulldogs - Riverside Brookfield
# Jr cougars
# Jr cyclones
# Jr patriots
# Jr Rebels
# Jr. Bulldogs
# Jr. Cyclones
# Jr. Kahoks
# JRW
# JRW Jake Reicin Wrestling
# Junior Bulldogs
# Junior Cyclones
# Junior Titans
# Junior Titans WC
# Kaneland Knights
# Kaneland Knights Wrestling Clu
# Katana
# KING SELECT
# Lake Zurich Cubs
# Lake Zurich Cubs Wrestling Clu
# Lake Zurich Wrestling Club
# LaSalle Peru Crunching Cavs Yo
# LaSalle Peru Crunching Cavs Youth
# Lawrence County Knights
# Lemont Bears
# Leyden Wolfpack
# Li'L Trojans WC
# Li`L Trojans WC
# Lil Reapers
# Lil Reapers Wrestling Club
# Lil` Coalers
# Lil` Coalers Wrestlng Club
# Lil` Reapers WC
# LIMESTONE
# Lincoln Youth Wrestling
# Lincolnway Wrestling Club
# Lions Wrestilng Club
# Litchfield Wrestling Foundatio
# Litchfield Wrestling Foundation
# Litchfield Wrestling Foundation Club
# Little Giant WC
# Little reapers Wrestling club
# Lockport jr Porters
# Lockport Jr Porters
# Lockport Junior Porters
# Lp crunching cavs
# LP Crunching Cavs
# LT Wrestling
# LWWC
# Macomb Little Bombers
# MACOMB LITTLE BOMBERS
# Maine Eagles
# Maritime Wrestling Academy
# Martinez Elite
# Martinez Fox Valley
# Martinez Fox Valley Elite
# Mat Rat
# Mattoon wrestling club
# Mauldin Wrestling Club
# McCracken County
# Mendota YMCA Mat Masters
# Meridian Hawks Youth Wrestling
# Meridian Hawks YW club
# Metamora
# Metamora Kids Club
# Midwest RTC (indiana)
# Midwest RTC (Indiana)
# Moline
# Moline wrestling
# Monticello Youth
# Monticello Youth Wrestling Clu
# Mt Zion kids club
# Mt Zion WC
# Mt. Zion Kids Club
# Munster Wrestling Club
# Mustangs WC
# MUSTANGS WC
# Mustangs Wrestling Club
# N.Y.A. Jr. Rebels
# Niceville
# Northview Wrestling Club
# Northwest Jr. Lions
# notre dame wrestling
# Notre Dame Wrestling
# NW GRAPPLERS (Missouri)
# nWo
# nWo Wrestling
# NWO Wrestling
# NYA Jr Rebels
# O`Fallon Little Panthers
# Oak Forest Warriors
# Oak Forest WC
# Oak Lawn Acorns
# Oakwood Youth Wrestling
# Olney Cubs
# Olympia
# Orland Park Pioneers
# Orland Park Pioneers (South Chicago)
# Orland Park Pioneers Wrestling
# Oswego Wrestling
# Ottawa Wolfpack
# Ozaukee
# P3 Warrior Wrestling
# Palatine wrestling club
# Palmyra Youth Wrestling Club
# Panther Paw Wrestling
# Panther Powerhouse
# Panther Powerhouse WC
# Parkview Albany Youth (WI)
# Pekin boys & girls club
# Peoria Heights Minutemen
# Peoria Razorbacks
# Peoria Razorbacks Wrestling Cl
# Peoria St. Philomena
# Peotone Little Devils
# Peotone Little Devils Wrestlin
# Petersburg
# Petersburg youth
# Petersburg Youth WC
# Petersburg Youth Wrestling
# Plano Lil Reapers
# Plano Little Reapers Wrestling Club
# Poplar Wrestling Club
# Prairie Central Youth Wrestlin
# Princeton Tigers
# Prior Lake Wrestling Club
# Prodigy Wrestling Club
# Proviso Township
# Proviso township gladiators
# PSF
# Purler Athletic Center
# Quincy Little Raiders Wrestlin
# Quincy Raiders
# Rantoul Jr. Eagles
# Rantoul Junior Eagles
# Raptors
# Red Devils WC
# Red Raiders
# Red Raiders (North)
# Red Raiders wrestling
# Red Raiders Wrestling
# red raiders wrestling club
# Red Raiders Wrestling Club
# Redraiders wrestling
# Region Wrestling Academy
# Relentless Wrestling
# Rhyno Academy
# Rhyno Academy of Wrestling
# Richmond
# Riot Room
# RIOT ROOM
# RIOT ROOM WC
# River Bend Wrestling
# Riverbend Wrestling Club
# Rochelle Wresting Club
# Rock Island Youth Wrestling
# Rockford Wrestling
# Rolling Meadows Park District
# Rollling Meadows park District
# Roughneck wc
# Roughneck Wrestling Club
# Roughnecks
# Round lake Jr panthers
# Round Lake Jr Panthers
# Round Lake Jr. Panthers Wrestling
# RWA
# Sabers WC
# Sabertooth WC (KY)
# Saint Charles North Wrestling Club
# Saint Charles Wreslting Club
# Saint Louis Jesuit Wrestling
# Sauk Valley
# Sauk Valley Wrestling
# SCN
# SCN (West Chicago)
# SCN Youth
# SCN Youth wrestling
# SCN Youth Wrestling
# Sharks Wrestling
# Shelbyville Jr Rams
# Shelbyville Jr. Rams Wrestling
# Sherrard Junior Tigers
# SJO
# SOT-C
# SOT-C/ The Compound
# South Gibson
# South Gibson Wrestling Club
# Southern IL Bulldogs
# Southern Illinois Bulldogs
# Southern Illinois Bulldogs (South)
# Southside Outlaws
# Southside Outlaws Wrestling Cl
# SOWA
# Sparta Jr Bulldogs
# Sparta Junior Bulldogs
# Sparta Junior Bulldogs Wrestli
# Springs Elite
# St. Charles
# St. Joes Jr Lancers
# St. Louis warriors
# St. Louis Warriors
# St.Charles Wrestling Club
# Stateline Stingers
# STCE
# STCWC
# Ste. Genevieve Youth Wrestling
# Stillman Valley
# Stl warrior
# Stl Warrior
# STL Warrior
# STL WARRIORS
# Stockton Renegades
# Stockton Renegades Wrestling
# Storm Youth Wrestling
# Streator bulldogs
# Streator Bulldogs
# Streator Bulldogs WC
# Stronghold (Alabama)
# Suplex
# Suplex City Raptors
# SWA
# Team 312
# Team Action
# Team El1te
# TEAM EL1TE
# Team El1te WC
# Team Honey Badger
# Team HoneyBadger
# Team Mascoutah
# Team Mascoutah Wrestling
# Team MO Mehlville Oakville
# Team Nazar
# Team Nazar (WI)
# Team Piasa
# Team Piasa Wrestling
# Tennessee - UN
# The Compound
# The Foundation
# The ICM Elite Wrestling Club
# The Island City Misfits Elite
# The Island of Misfit
# The Law
# The LAW
# Thoroughbred Wrestling Academy
# Tiger Elite Wrestling
# TIGER ELITE WRESTLING
# Tiger Town Tangler WC
# Tiger Town Tanglers
# Tiger Town Tanglers (Princeton
# Tiger Town Tanglers Wrestling
# Tiger Training Center
# Tigertown Tanglers - Princeton
# TIMBER WOLVES WRESTLING
# Tinley Park Bulldogs
# Tinley Park Bulldogs  (Central Chicago)
# Tinley Park Bulldogs Wrestling
# TJ Trained
# TJ Trained - Clinton
# TJ Trained Clinton
# TJ Trained-Clinton
# Toledo Trained
# Tony Capriola Sr. Wrestling Cl
# Tony Capriola Sr. Wrestling Club
# Tornado WC
# Toss Em Up (Wisconsin)
# Trevian
# Trevians Wrestling Club
# Trico
# Twin City Tigers
# Unattached
# Union county Elite Braves
# Union County Wrestling Club
# Unity Youth Wrestling
# Urbana Tigers Wrestling Club
# Vandalia jr vandals
# Victory Elite
# Villa Park Young Warriors
# Villa Park Young Warriors Wres
# Vittum Cats
# Vittum Cats (Central Chicago)
# Vortex Wrestling
# Warrensburg-Latham Jr. Cardina
# Wave Wrestling Club
# WC Lightning
# WC Lightning Wrestling Club
# Wentzville Wrestling Fed.
# Wentzville Wrestling Federatio
# Wentzville Wrestling Federation
# West Frankfort JR Redbirds
# West Plains Wrestling Club
# West Suburban Girls
# West Suburban Girls Wrestling
# West Suburban Wrestling Club
# Western Indiana
# Western Wrestling Club
# Westosha Wrestling Club
# Westville WC
# Wheeling Wildcats
# Wheeling wildcats WC
# Wheeling Wildcats WC
# Wheeling wrestling club
# Wildcat Wrestling Academy
# Wildcats WA
# Will County
# Will county warriors
# Will County Warriors
# Will County Warriors Wrestling
# Wilmot Jr. Panthers
# Wolfpack WC
# Wolfpack Wrestling Club
# Woodstock cyclones
# Woodstock Cyclones
# Woodstock Cyclones wrestling
# WreStl
# WreSTL
# Wright City Jr Wildcats
# WWF
# Xtreme
# Yorkville
# Young guns
# Young Warrior WA
# Young Warrior Wrestling Academ
# Young Warriors
# Young warriors wrestling acade
# Young Warriors Wrestling Academy
# Zumwalt


def _load_matches() -> list[bracket_util.Match]:
    input_file = _ROOT / "_parsed-data" / "all-matches-01.csv"
    with open(input_file) as file_obj:
        rows = list(csv.DictReader(file_obj))

    for row in rows:
        if row["Division"] == "":
            row["Division"] = None

    matches_root = bracket_util.Matches.model_validate(rows)
    return matches_root.root


def _load_rosters() -> list[club_util.ClubInfo]:
    input_file = _ROOT / "_parsed-data" / "rosters.json"
    with open(input_file) as file_obj:
        as_json = file_obj.read()

    clubs_root = club_util.Clubs.model_validate_json(as_json)
    return clubs_root.root


def _normalize_name(name: str) -> str:
    case_insensitive = name.lower()

    parts = case_insensitive.split()
    whitespace_normalized = " ".join(parts)

    without_punctuation = whitespace_normalized.replace("'", "")
    without_punctuation = without_punctuation.replace(".", "")
    without_punctuation = without_punctuation.replace(",", "")
    without_punctuation = without_punctuation.replace("&", "and")
    without_punctuation = without_punctuation.replace("-", " ")
    without_punctuation = without_punctuation.replace("`", "")
    # NOTE: `c/ ` is a special case based on a likely typo in real data
    without_punctuation = without_punctuation.replace("c/ ", "c ")

    without_punctuation = without_punctuation.replace(" (", " ")
    without_punctuation = without_punctuation.replace(") ", " ")
    without_punctuation = without_punctuation.replace(" / ", " ")
    if without_punctuation.startswith("("):
        without_punctuation = without_punctuation[1:]
    if without_punctuation.endswith(")"):
        without_punctuation = without_punctuation[:-1]

    if _SIMPLE_NAME.match(without_punctuation) is None:
        raise RuntimeError("Unhandled name needs normalized", name, without_punctuation)

    parts = without_punctuation.split()
    whitespace_normalized = " ".join(parts)

    return whitespace_normalized


def _prepare_club_lookup(rosters: list[club_util.ClubInfo]) -> dict[str, str]:
    club_name_lookup = {
        _normalize_name(roster.club_name): roster.club_name for roster in rosters
    }
    if len(club_name_lookup) != len(rosters):
        raise RuntimeError("Non-unique club names")

    # First pass: WC and "Wrestling Club" synonym
    keys = sorted(club_name_lookup.keys())
    for key in keys:
        new_key = None
        if "wrestling club" in key:
            new_key = key.replace("wrestling club", "wc")
        elif key.endswith(" wc"):
            new_key = key[:-2] + "wrestling club"

        if new_key is None:
            continue

        if new_key in club_name_lookup:
            raise ValueError("Unexpected collision", key, new_key)
        club_name_lookup[new_key] = club_name_lookup[key]

    # Second pass: Jr. and "Junior" synonym
    keys = sorted(club_name_lookup.keys())
    for key in keys:
        new_key = None
        if " jr " in key:
            new_key = key.replace(" jr ", " junior ")
        elif key.startswith("jr "):
            new_key = "junior" + key[2:]
        elif " junior " in key:
            new_key = key.replace(" junior ", " jr ")
        elif key.startswith("junior "):
            new_key = "jr" + key[6:]

        if new_key is None:
            continue

        if new_key in club_name_lookup:
            raise ValueError("Unexpected collision", key, new_key)
        club_name_lookup[new_key] = club_name_lookup[key]

    return club_name_lookup


def _lookup_team(team: str, club_name_lookup: dict[str, str]) -> str | None:
    if team == "":
        return None

    team_normalized = _normalize_name(team)
    matched = club_name_lookup.get(team_normalized)
    if matched is not None:
        return matched

    partial_matches = {
        value for key, value in club_name_lookup.items() if key in team_normalized
    }
    if len(partial_matches) == 1:
        return list(partial_matches)[0]

    if partial_matches == set(_FALSE_DUPLICATE_CARDINAL):
        return "Arlington Cardinals Wrestling Club"

    if len(partial_matches) > 1:
        raise RuntimeError("Unexpected duplicates", team, partial_matches)

    return None


def _lookup_teams(
    match: bracket_util.Match, club_name_lookup: dict[str, str]
) -> tuple[str | None, str | None]:
    winner_team_matched = _lookup_team(match.winner_team, club_name_lookup)
    loser_team_matched = _lookup_team(match.loser_team, club_name_lookup)
    return winner_team_matched, loser_team_matched


def main() -> None:
    matches = _load_matches()
    print(len(matches))

    rosters = _load_rosters()
    club_name_lookup = _prepare_club_lookup(rosters)

    for match in matches:
        _lookup_teams(match, club_name_lookup)


if __name__ == "__main__":
    main()
