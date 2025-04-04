import streamlit as st
import currentslate
import currentslatehitters
import tkinter as tk
from tkinter import filedialog
import pandas as pd
from scipy.stats import norm
import statistics

historicdata = pd.read_csv("historic_data.csv")
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename()
file = open(file_path)
hitterdf = currentslatehitters.currentslatehitters(file)
hitterdf = hitterdf.drop(0)
file = open(file_path)
pitcherdf = currentslate.currentslate(file)
file = open(file_path)
matchupdf = pd.read_csv(file)
pitcherdf = pitcherdf.drop(index=0)
pitcherdf["K% Rank"] = pitcherdf["K%"].rank(method='average',ascending=False)
pitcherdf["BB% Rank"] = pitcherdf["BB%"].rank(method='average',ascending=True)
pitcherdf["SwStr% Rank"] = pitcherdf["SwStr%"].rank(method='average',ascending=False)
pitcherdf["IP/G Rank"] = pitcherdf["IP/G"].rank(method='average',ascending=False)
pitcherdf["xFIP Rank"] = pitcherdf["xFIP"].rank(method='average',ascending=True)
pitcherdf["ParkFactor Rank"] = pitcherdf["ParkFactor"].rank(method='average',ascending=True)
pitcherdf["Total Rank"] = pitcherdf[["K% Rank","BB% Rank","SwStr% Rank","IP/G Rank","xFIP Rank","ParkFactor Rank"]].dot([.25,.05,.10,.30,.20,.10])
pitcherdf["Rank"] = pitcherdf["Total Rank"].rank(method="average",ascending=True)
teams =[]
opponents =[]
for pitcher in pitcherdf["Name"].to_list():
    teams.append(matchupdf[matchupdf["Nickname"] == pitcher]["Team"].values[0])
    opponents.append(matchupdf[matchupdf["Nickname"] == pitcher]["Opponent"].values[0])
pitcherdf["Team"] = teams
pitcherdf["Opponent"] = opponents
pitcherdf = pitcherdf[["Name","Team","Opponent","Rank","K%"]]
maxrank = max(pitcherdf["Rank"])
projections = []
alldata = []
for index, row in hitterdf.iterrows():
    name = row["Hitter"]
    woba = row["wOBA"]
    battingorder = matchupdf[matchupdf["Nickname"] == name]["Batting Order"].values[0]
    position = matchupdf[matchupdf["Nickname"] == name]["Roster Position"].values[0]
    salary = matchupdf[matchupdf["Nickname"] == name]["Salary"].values[0]
    team = matchupdf[matchupdf["Nickname"] == name]["Team"].values[0]
    opponent = matchupdf[matchupdf["Nickname"] == name]["Opponent"].values[0]
    opp_pitchrank = pitcherdf[pitcherdf["Team"] == opponent]["Rank"].values[0]
    floorminus = (maxrank - opp_pitchrank + 1) * 0.05/(maxrank/2)
    ceilingplus = opp_pitchrank * 0.05/(maxrank/2)
    cdf = norm.cdf(x = woba, loc = statistics.mean(historicdata["wOBA"]), scale = statistics.stdev(historicdata["wOBA"]))
    ceiling = norm.ppf(q = min(0.99, cdf + ceilingplus), loc = statistics.mean(historicdata["wOBA"]), scale = statistics.stdev(historicdata["wOBA"]))
    floor = norm.ppf(q = max(0.01, cdf - floorminus), loc = statistics.mean(historicdata["wOBA"]), scale = statistics.stdev(historicdata["wOBA"]))
    projection = statistics.mean(historicdata[(historicdata["wOBA"] <= ceiling) & (historicdata["wOBA"] >= floor)]["FDScore"].values)
    alldata.append([name,battingorder,salary,position,team,opponent,projection])

alldatadf = pd.DataFrame(alldata,columns=["Name","Batting Order","Salary","Position","Team","Opponent","Projection"])

hitterteams = list(pd.unique(alldatadf["Team"]))

teamsummary =[]
for team in hitterteams:
    filtered = alldatadf[alldatadf["Team"] == team]
    top = filtered.head(5)
    proj = sum(top["Projection"])
    salary = sum(top["Salary"])
    teamsummary.append([team,proj,salary,proj/salary*1000])
teamsummarydf = pd.DataFrame(teamsummary,columns=["Team","Projection","Salary","Value"])
