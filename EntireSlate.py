import streamlit as st
import currentslate
import currentslatehitters
import pandas as pd
from scipy.stats import norm
import statistics


st.set_page_config(
    layout="wide",
)

@st.cache_data
def dataload(file):
    matchupdf = pd.read_csv(file)
    historicdata = pd.read_csv("historic_data.csv")
    hitterdf = currentslatehitters.currentslatehitters(matchupdf)
    hitterdf = hitterdf.drop(0)
    pitcherdf = currentslate.currentslate(matchupdf)
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
    pitcherdf = pitcherdf[["Name","Team","Opponent","K%","Rank"]]
    maxrank = max(pitcherdf["Rank"])
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
        alldata.append([name,battingorder,salary,position,team,opponent,projection,projection/salary*1000])

    alldatadf = pd.DataFrame(alldata,columns=["Name","Batting Order","Salary","Position","Team","Opponent","Projection","Value"])
    alldatadf = alldatadf.sort_values(by="Projection",ascending=False)
    return alldatadf, pitcherdf

def teamsummary(alldatadf):
    hitterteams = list(pd.unique(alldatadf["Team"]))
    teamsummary =[]
    for team in hitterteams:
        filtered = alldatadf[alldatadf["Team"] == team]
        top = filtered.head(5)
        proj = sum(top["Projection"])
        salary = sum(top["Salary"])
        teamsummary.append([team,proj,salary,proj/salary*1000])
    teamsummarydf = pd.DataFrame(teamsummary,columns=["Team","Projection","Salary","Value"])
    teamsummarydf = teamsummarydf.sort_values(by="Projection",ascending=False)
    return teamsummarydf

def pitchersummary(pitcherdf, teamsummarydf):
    teamsummarydf["Opponent Rank"] = teamsummarydf["Projection"].rank(method="average",ascending=False)
    maxrank = max(teamsummarydf["Opponent Rank"])
    teamsummarydf = teamsummarydf[["Team","Opponent Rank"]]
    teamsummarydf = teamsummarydf.rename({"Team":"Opponent"},axis=1)
    pitcherdf = pd.merge(pitcherdf,teamsummarydf,how="inner",on="Opponent")
    print(pitcherdf)
    pitcherdf["Total Rank"] = pitcherdf["Rank"] + (maxrank - pitcherdf["Opponent Rank"])
    pitcherdf["Total Rank"] = pitcherdf["Total Rank"].rank(method="average",ascending=True)
    return pitcherdf

def top_fourstacks(alldatadf):
    hitterteams = list(pd.unique(alldatadf["Team"]))
    stackprojections = []
    stacks = [[1,2,3,4],
              [2,3,4,5],
              [3,4,5,6],
              [1,2,4,5],
              [2,4,5,6],
              [1,3,4,5],
              [1,2,3,5],
              [2,3,5,6],
              [9,1,2,3],
              [9,1,2,4],
              [9,1,3,4],
              [9,2,3,4],
              [1,3,5,6]]
    for team in hitterteams:
        for stack in stacks:
            filtered = alldatadf[(alldatadf["Team"] == team) & (alldatadf["Batting Order"].isin(stack))]
            proj = sum(filtered["Projection"])
            salary = sum(filtered["Salary"])
            namelist = list(filtered["Name"].values)
            stackprojections.append([stack,team,proj,salary,proj/salary*1000,namelist])
    stacksdf = pd.DataFrame(stackprojections, columns=["Stack","Team","Projection","Salary","Value","Hitters"])
    stacksdf = stacksdf.sort_values(by="Projection",ascending=False)
    return stacksdf
        


st.title("Data!")
all_players = st.file_uploader("Upload FD CSV")
alldatadf, pitcherdf = dataload(all_players)
teamsummarydf = teamsummary(alldatadf)
pitchersummarydf = pitchersummary(pitcherdf,teamsummarydf)
stacksdf = top_fourstacks(alldatadf)
st.dataframe(alldatadf, hide_index = True)
st.write("-"*100)
st.dataframe(pitchersummarydf, hide_index = True)
st.write("-"*100)
st.dataframe(teamsummarydf,hide_index = True)
st.write("--"*100)
st.dataframe(stacksdf, hide_index=True, width=1500)


