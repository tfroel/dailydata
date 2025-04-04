import mlbstatsapi
import pandas as pd
from datetime import datetime
from datetime import timedelta
from bs4 import BeautifulSoup as bs
import requests
import ast
import tkinter as tk
from tkinter import filedialog


def currentslatehitters(file):
    mlb = mlbstatsapi.Mlb()
    FD = pd.read_csv(file)
    FD = FD[FD["Position"] != "P"]
    FD = FD[FD["Injury Indicator"] != "O"]
    FD = FD[FD["Injury Indicator"] != "IL"]
    hitters = FD["Nickname"]
    issuenames = []

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



    totaldf = pd.DataFrame([["","","","","","","",""]],columns=["Hitter","SLG","OPS","BB%","K%","RBI%","wOBA","PA/HR"])
    for hitter in hitters:
        try:
            hitteridname = names[hitter]
            id = mlb.get_people_id(hitteridname)[0]
            params = {"season":2025,
                    "limit":60}
            stat_dict = mlb.get_player_stats(id,stats=["lastXGames"],groups=["hitting"],**params)
            try: 
                lastx = stat_dict["hitting"]["lastxgames"].splits[-1].stat
                lastxpas = lastx.plateappearances
                lastxabs = lastx.atbats
                lastxhrs = lastx.homeruns
                lastxgames = lastx.gamesplayed
                lastxks = lastx.strikeouts
                lastxslgnum = float(lastx.slg)*lastxabs
                lastxopsnum = float(lastx.ops)*lastxabs*(lastxabs+lastx.baseonballs+lastx.sacflies+lastx.hitbypitch)
                lastxrbi = lastx.rbi
                lastxbb = lastx.baseonballs
                lastxlob = lastx.leftonbase
                lastxubb = lastx.baseonballs-lastx.intentionalwalks
                lastxhbp = lastx.hitbypitch
                lastxsingles = lastx.hits-lastx.doubles-lastx.triples-lastx.homeruns
                lastxdoubles = lastx.doubles
                lastxtriples = lastx.triples
                lastxsacflies = lastx.sacflies
            except:
                lastxgames = None
            if lastxgames == None:
                params = {
                    "season":2024,
                    "limit":60}
                try:
                    lxstat_dict = mlb.get_player_stats(id,stats=["lastXGames"],groups=["hitting"],**params)
                    lastx = lxstat_dict["hitting"]["lastxgames"].splits[-1].stat
                    lastxpas = lastx.plateappearances
                    lastxabs = lastx.atbats
                    lastxks = lastx.strikeouts
                    lastxhrs = lastx.homeruns
                    lastxgames = lastx.gamesplayed
                    lastxslgnum = float(lastx.slg)*lastxabs
                    lastxopsnum = float(lastx.ops)*lastxabs*(lastxabs+lastx.baseonballs+lastx.sacflies+lastx.hitbypitch)
                    lastxrbi = lastx.rbi
                    lastxbb = lastx.baseonballs
                    lastxlob = lastx.leftonbase
                    lastxubb = lastx.baseonballs-lastx.intentionalwalks
                    lastxhbp = lastx.hitbypitch
                    lastxsingles = lastx.hits-lastx.doubles-lastx.triples-lastx.homeruns
                    lastxdoubles = lastx.doubles
                    lastxtriples = lastx.triples
                    lastxsacflies = lastx.sacflies    
                except:
                    pass
            if lastxgames < 60:
                params = {
                    "season":2024,
                    "limit":60-lastxgames}
                lxstat_dict = mlb.get_player_stats(id,stats=["lastXGames"],groups=["hitting"],**params)
                try:
                    lastx = lxstat_dict["hitting"]["lastxgames"].splits[-1].stat
                    lastxpas += lastx.plateappearances
                    lastxabs += lastx.atbats
                    lastxhrs += lastx.homeruns
                    lastxgames += lastx.gamesplayed
                    lastxks += lastx.strikeouts
                    lastxslgnum = float(lastx.slg)*lastxabs
                    lastxopsnum = float(lastx.ops)*lastxabs*(lastxabs+lastx.baseonballs+lastx.sacflies+lastx.hitbypitch)
                    lastxrbi += lastx.rbi
                    lastxlob += lastx.leftonbase
                    lastxbb += lastx.baseonballs
                    lastxubb += lastx.baseonballs-lastx.intentionalwalks
                    lastxhbp += lastx.hitbypitch
                    lastxsingles += lastx.hits-lastx.doubles-lastx.triples-lastx.homeruns
                    lastxdoubles += lastx.doubles
                    lastxtriples += lastx.triples
                    lastxsacflies += lastx.sacflies 
                except:
                    pass
            rbiperc = (lastxrbi - lastxhrs)/(lastxrbi-lastxhrs+lastxlob)
            woba = (0.689*lastxubb + 0.720*lastxhbp+0.882*lastxsingles+1.254*lastxdoubles+1.590*lastxtriples+2.050*lastxhrs)/(lastxabs+lastxubb+lastxsacflies+lastxhbp)
            lastxslg = lastxslgnum/lastxabs
            lastxops = lastxopsnum/(lastxabs*(lastxabs+lastxbb+lastxsacflies+lastxhbp))
            lastxbbperc = lastxubb/lastxpas
            lastxkperc = lastxks/lastxpas
            try:
                output = [hitter,float(lastxslg),float(lastxops),float(lastxbbperc),float(lastxkperc),float(rbiperc),float(woba),float(lastxpas/lastxhrs)]
                totaldf.loc[len(totaldf)] = output
                totaldf.to_csv("currentslatehitters.csv")
            except:
                print("write_error",hitter)
                pass
        except:
            print("code error")
            pass
    return totaldf
    