import mlbstatsapi
import pandas as pd
from datetime import datetime
from datetime import timedelta
from bs4 import BeautifulSoup as bs
import requests
import ast
import tkinter as tk
from tkinter import filedialog


def currentslate(file):
    parkfactors = pd.read_csv("parkfactors.csv")
    mlb = mlbstatsapi.Mlb()
    FD = pd.read_csv(file)
    FD = FD[FD["Probable Pitcher"] == "Yes"]
    starters = FD["Nickname"]
    matchups = FD["Game"].to_list()
    teams = []
    names ={}
    accentdict ={
        "à":"a",
        "è":"e",
        "ì":"i",
        "ò":"o",
        "ù":"u",
        "á":"a",
        "é":"e",
        "í":"i",
        "ó":"o",
        "ú":"u",
        "ñ":"n",
        "ã":"a",
        "õ":"o"
    }
    for player in mlb.get_people():
        basicname = player.fullname
        for letter in list(accentdict.keys()):
            basicname = basicname.replace(letter,accentdict[letter])
        actualname = player.fullname
        names[basicname] = actualname
    for game in matchups:
        teams.append(game.split("@")[-1])
    startlist = starters.to_list()
    totaldf = pd.DataFrame([["","","","","","",""]],columns=["Name","K%","BB%","SwStr%","IP/G","xFIP","ParkFactor"])
    for name in starters:
        team = teams[startlist.index(name)]
        pf = parkfactors[parkfactors["Team"] == team]["Park Factor"].values[0]
        spidname = names[name]
        spid = mlb.get_people_id(spidname)[0]
        link_brd = "https://statsapi.mlb.com/api/v1/people/" + str(spid) + "/stats?stats=sabermetrics&season=2024"
        r = requests.get(link_brd)
        soup = bs(r.content,"html.parser")
        statdict = ast.literal_eval(soup.contents[0])
        statdict = statdict["stats"][0]["splits"][-1]["stat"]
        xfip = statdict["xfip"]
        try:
            pparams = {
            "season":2025,
            "startDate":"2025-01-01",
            "endDate":"2025-12-31"
            }
            flyballs = 0
            plstatdict = mlb.get_player_stats(spid,stats=["pitchLog"],groups=["pitching"],**pparams)
            allpitches = plstatdict["pitching"]["pitchlog"].splits
            for pitch in allpitches:
                if pitch.stat.details.isinplay == True:
                    desc = pitch.stat.details.description
                    if " fly " in desc or " flies " in desc or " pop" in desc:
                        flyballs += 1
        except:
            flyballs = None
        link_brd = "https://statsapi.mlb.com/api/v1/people/" + str(spid) + "/stats?stats=lastXGames&season=2025"
        r = requests.get(link_brd)
        soup = bs(r.content,"html.parser")
        games23 = 0
        games24 = 0
        try:
            statdict = ast.literal_eval(soup.contents[0])
            statdict = statdict["stats"][0]["splits"][-1]["stat"]
            games = statdict["gamesPlayed"]
            games24 = statdict["gamesPlayed"]
            ks = statdict["strikeOuts"]
            bbs = statdict["baseOnBalls"]
            tbf = statdict["battersFaced"]
            ips = statdict["outs"]
            hbps = statdict["hitByPitch"]
            ers = statdict["earnedRuns"]
            hrs = statdict["homeRuns"]
        except:
            games = None
        if games == None:
            link_lx = "https://statsapi.mlb.com/api/v1/people/" + str(spid) + "/stats?stats=lastXGames&season=2024&limit=15"
            r = requests.get(link_lx)
            soup = bs(r.content,"html.parser")
            statdict = ast.literal_eval(soup.contents[0])
            statdict = statdict["stats"][0]["splits"][-1]["stat"]
            games = statdict["gamesPlayed"]
            games23 = statdict["gamesPlayed"]
            ks = statdict["strikeOuts"]
            bbs = statdict["baseOnBalls"]
            tbf = statdict["battersFaced"]
            ips = statdict["outs"]
            hbps = statdict["hitByPitch"]
            ers = statdict["earnedRuns"]
            hrs = statdict["homeRuns"]
        elif games < 15:
            link_lx = "https://statsapi.mlb.com/api/v1/people/" + str(spid) + "/stats?stats=lastXGames&season=2024&limit=" + str(15-games)
            r = requests.get(link_lx)
            soup = bs(r.content,"html.parser")
            statdict = ast.literal_eval(soup.contents[0])
            statdict = statdict["stats"][0]["splits"][-1]["stat"]
            games += statdict["gamesPlayed"]
            games23 = statdict["gamesPlayed"]
            ks += statdict["strikeOuts"]
            bbs += statdict["baseOnBalls"]
            tbf += statdict["battersFaced"]
            ips += statdict["outs"]
            hbps += statdict["hitByPitch"]
            ers += statdict["earnedRuns"]
            hrs += statdict["homeRuns"]
        ips = ips/3
        params = {
            "season":2024
        }
        s23 = mlb.get_player_stats(spid,stats=["season","seasonAdvanced"],groups=["pitching"],**params) 
        s23std = s23["pitching"]["season"].splits[-1].stat
        s23adv = s23["pitching"]["seasonadvanced"].splits[-1].stat

        try:
            params = {
            "season":2025
        }
            s24 = mlb.get_player_stats(spid,stats=["season","seasonAdvanced"],groups=["pitching"],**params) 
            s24std = s24["pitching"]["season"].splits[-1].stat
            s24adv = s24["pitching"]["seasonadvanced"].splits[-1].stat
        except:
            pass
        whiff23 = s23adv.swingandmisses
        pitches23 = s23std.numberofpitches
        try:
            whiff = s24adv.swingandmisses
            pitches = s24std.numberofpitches
        except:
            whiff = 0
            pitches = 0
        if flyballs == None or games24 < 15:
            xfip = xfip
        else:
            xfip = ((13*flyballs*0.12) + (3*(bbs+hbps)) - (2*(ks)))/ips + 3.2
        k_ratio = ks/tbf*100
        bb_ratio = bbs/tbf*100
        swstr_ratio23 = whiff23/pitches23*100
        try:
            swstr_ratio = whiff/pitches*100
        except:
            swstr_ratio = 0
        hr_ratio = hrs/tbf*100
        era = ers/ips*9
        swstr_ratio = swstr_ratio*(games24/(games23+games24)) + swstr_ratio23*(games23/(games23+games24))
        ipg_ratio = ips/games
        output = [name, float(k_ratio),float(bb_ratio),float(swstr_ratio),float(ipg_ratio),float(xfip),int(pf)]
        totaldf.loc[len(totaldf)] = output
        totaldf.to_csv("currentslate.csv")
    return totaldf
        