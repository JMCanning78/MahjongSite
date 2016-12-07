#!/usr/bin/env python3

import json
import db
import random
import datetime
from operator import itemgetter

from flask import render_template, session, request, Response
from MahjongSite import app

@app.route('/seating')
def Seating():
    if request.method == "GET":
        return render_template("seating.html")

@app.route('/seating/regentables', methods=["POST"])
def RegenTables():
    with db.getCur() as cur:
        cur.execute("SELECT PlayerId FROM CurrentPlayers")
        players = []
        for row in cur.fetchall():
            players += [row[0]]
        playergames = playerGames(players, cur)
        tables = bestArrangement(players, playergames)
        cur.execute("DELETE FROM CurrentTables")
        comma = False
        for player in tables:
            comma = True
            cur.execute("INSERT INTO CurrentTables(PlayerId) VALUES(?)", (player,))
        return Response('{"status":0}', mimetype = 'application/json')

@app.route('/seating/currentplayers.json')
def CurrentPlayers():
    with db.getCur() as cur:
        cur.execute("SELECT Name FROM CurrentPlayers INNER JOIN Players ON PlayerId = Players.Id ORDER BY Players.Name")
        return Response(json.dumps(map(lambda x:x[0], cur.fetchall())), mimetype = 'application/json')

@app.route('/seating/addcurrentplayer', methods = ["POST"])
def AddCurrentPlayer():
    if not 'player' in request.form:
        return Response('{"status":1,"error":"Please enter a player"}', mimetype = 'application/json')

    player = request.form['player']

    with db.getCur() as cur:
        cur.execute("SELECT Id FROM Players WHERE Id = ? OR Name = ?", (player, player))
        row = cur.fetchone()
        if row is None or len(row) == 0:
            cur.execute("INSERT INTO Players(Name) VALUES(?)", (player,))
            cur.execute("SELECT Id FROM Players WHERE Name = ?", (player,))
            row = cur.fetchone()
            return
        player = row[0]

        cur.execute("SELECT COUNT(*) FROM CurrentPlayers WHERE PlayerId = ?", (player,))
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO CurrentPlayers(PlayerId) VALUES(?)", (player,))
        return Response('{"status":0}', mimetype = 'application/json')

@app.route('/seating/removeplayer', methods = ["POST"])
def RemovePlayer():
    if not 'player' in request.form:
        return Response('{"status":1,"error":"Please enter a player"}', mimetype = 'application/json')

    player = request.form['player']

    with db.getCur() as cur:
        cur.execute("DELETE FROM CurrentPlayers WHERE PlayerId IN (SELECT Id FROM Players WHERE Players.Id = ? OR Players.Name = ?)", (player, player))
        return Response('{"status":0}', mimetype = 'application/json')

@app.route('/seating/clearcurrentplayers', methods = ["POST"])
def ClearCurrentPlayers():
    with db.getCur() as cur:
        cur.execute("DELETE FROM CurrentPlayers")
        cur.execute("DELETE FROM CurrentTables")
        return Response('{"status":0}', mimetype = 'application/json')

@app.route('/seating/currenttables.json')
def CurrentTables():
    with db.getCur() as cur:
        cur.execute("SELECT Players.Name FROM CurrentTables INNER JOIN Players ON Players.Id = CurrentTables.PlayerId")
        return Response(json.dumps(cur.fetchall()), mimetype = 'application/json')


@app.route('/seating/players.json')
def PlayersList():
    with db.getCur() as cur:
        cur.execute("SELECT Name FROM Players ORDER BY Name")
        return Response(json.dumps(map(lambda x:x[0], cur.fetchall())), mimetype = 'application/json')

POPULATION = 256

def bestArrangement(tables, playergames, population = POPULATION):
    numplayers = len(tables)

    tabless = []
    for i in range(POPULATION):
        tables = tables[:]
        random.shuffle(tables)
        tabless += [(tablesScore(tables, playergames), tables)]
    tabless.sort(key=itemgetter(0))

    minScore = tabless[0][0]
    return tabless[0][1]
    improved = 0

    while improved < numplayers and minScore > 0:
        for j in range(POPULATION):
            newTables = mutateTables(tabless[j][1])
            tabless += [(tablesScore(newTables, playergames), newTables)]
        tabless.sort(key=itemgetter(0))
        tabless = tabless[0:POPULATION]

        improved += 1
        if minScore != tabless[0][0]:
            minScore = tabless[0][0]
            improved = 0

    return tabless[0][1]

def mutateTables(tables):
    tables = tables[:]
    a = random.randint(0, len(tables) - 1)
    b = random.randint(0, len(tables) - 1)
    tables[a], tables[b] = tables[b], tables[a]

    return tables

def tablesScore(players, playergames):
    numplayers = len(players)
    if numplayers >= 8:
        tables_5p = numplayers % 4
        total_tables = int(numplayers / 4)
        tables_4p = total_tables - tables_5p
    else:
        if numplayers >= 5:
            tables_5p = 1
        else:
            tables_5p = 0
        total_tables = 1
        tables_4p = total_tables - tables_5p

    score = 0

    for i in range(0, tables_5p * 5, 5):
        table = players[i:i+5]
        score += tableScore(table, playergames)

    for i in range(tables_5p * 5, numplayers, 4):
        table = players[i:i+4]
        score += tableScore(table, playergames)

    return score

def tableScore(players, playergames):
    numplayers = len(players)

    score = 0
    for i in range(numplayers):
        for j in range(i + 1, numplayers):
            if (players[i], players[j]) in playergames:
                score += playergames[(players[i], players[j])]
            elif (players[j], players[i]) in playergames:
                score += playergames[(players[j], players[i])]
    return score

def playerGames(players, c):
    numplayers = len(players)

    playergames = dict()
    now = datetime.datetime.now()
    now = str(now.year) + " " + str((now.month - 1) / 3)

    for i in range(numplayers):
        for j in range(i + 1, numplayers):
            games = c.execute("SELECT COUNT(*) FROM Scores WHERE PlayerId = ? AND GameId IN (SELECT GameId FROM Scores WHERE PlayerId = ?) AND strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 3) = ?", (players[i], players[j], now)).fetchone()[0]
            if games != 0:
                playergames[(players[i], players[j])] = games

    return playergames
