#!/usr/bin/env python3

import tornado.web
import db
import random
import datetime
from operator import itemgetter

class SeatingHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("seating.html")

class RegenTables(tornado.web.RequestHandler):
    def post(self):
        self.set_header('Content-Type', 'application/json')
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
            self.write('{"status":0}')

class CurrentPlayers(tornado.web.RequestHandler):
    def get(self):
        with db.getCur() as cur:
            self.set_header('Content-Type', 'application/json')
            cur.execute("SELECT Name FROM CurrentPlayers INNER JOIN Players ON PlayerId = Players.Id ORDER BY Players.Name")
            self.write("[")
            comma = False
            for row in cur.fetchall():
                if comma:
                    self.write(",")
                comma = True
                self.write('"' + str(row[0]) + '"')
            self.write("]")


class AddCurrentPlayer(tornado.web.RequestHandler):
    def post(self):
        player = self.get_argument('player', None)

        if player is None or player == "":
            self.write('{"status":1,"error":"Please enter a player"}')
            return

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
            self.write('{"status":0}')

class RemovePlayer(tornado.web.RequestHandler):
    def post(self):
        player = self.get_argument('player', None)

        if player is None:
            self.write('{"status":1,"error":"Please enter a player"}')
            return

        with db.getCur() as cur:
            cur.execute("DELETE FROM CurrentPlayers WHERE PlayerId IN (SELECT Id FROM Players WHERE CurrentPlayers.PlayerId = Players.Id AND (Players.Id = ? OR Players.Name = ?))", (player, player))
            self.write('{"status":0}')

class ClearCurrentPlayers(tornado.web.RequestHandler):
    def post(self):
        with db.getCur() as cur:
            cur.execute("DELETE FROM CurrentPlayers")
            cur.execute("DELETE FROM CurrentTables")
            self.set_header('Content-Type', 'application/json')
            self.write('{"status":0}')

class CurrentTables(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'application/json')
        with db.getCur() as cur:
            cur.execute("SELECT Players.Name FROM CurrentTables INNER JOIN Players ON Players.Id = CurrentTables.PlayerId")
            self.write("[")
            comma = False
            for player in cur.fetchall():
                if comma:
                    self.write(",")
                comma = True
                self.write('"' + str(player[0]) + '"')
            self.write("]")


class PlayersList(tornado.web.RequestHandler):
    def get(self):
        with db.getCur() as cur:
            self.set_header('Content-Type', 'application/json')
            cur.execute("SELECT Id, Name FROM Players ORDER BY Name")
            self.write("[")
            comma = False
            for row in cur.fetchall():
                if comma:
                    self.write(",")
                comma = True
                self.write('"'+ row[1] + '"')
            self.write("]")

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

    for i in range(numplayers):
        for j in range(i + 1, numplayers):
            games = c.execute("SELECT COUNT(*) FROM Scores WHERE PlayerId = ? AND GameId IN (SELECT GameId FROM Scores WHERE PlayerId = ?) AND strftime('%Y', Date) = ?", (players[i], players[j], datetime.datetime.now().strftime('%Y'))).fetchone()[0]
            if games != 0:
                playergames[(players[i], players[j])] = games

    return playergames
