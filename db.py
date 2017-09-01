#!/usr/bin/env python3

import warnings
import sqlite3
import random
import datetime

import util
import settings

class getCur():
    con = None
    cur = None
    def __enter__(self):
        self.con = sqlite3.connect(settings.DBFILE)
        self.cur = self.con.cursor()
        return self.cur
    def __exit__(self, type, value, traceback):
        if self.cur and self.con and not value:
            self.cur.close()
            self.con.commit()
            self.con.close()

        return False

def init():
    warnings.filterwarnings('ignore', r'Table \'[^\']*\' already exists')

    with getCur() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS Players(Id INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT, MeetupName TEXT);")

        cur.execute("CREATE TABLE IF NOT EXISTS Scores(Id INTEGER PRIMARY KEY AUTOINCREMENT, GameId INTEGER, PlayerId INTEGER, Rank TINYINT, PlayerCount TINYINT, RawScore INTEGER, Score REAL, Date DATE, Chombos INTEGER, Quarter TEXT,\
            FOREIGN KEY(PlayerId) REFERENCES Players(Id) ON DELETE CASCADE);")

        cur.execute("CREATE TABLE IF NOT EXISTS CurrentPlayers(PlayerId INTEGER PRIMARY KEY, Priority TINYINT,\
            FOREIGN KEY(PlayerId) REFERENCES Players(Id) ON DELETE CASCADE);")

        cur.execute("CREATE TABLE IF NOT EXISTS CurrentTables(Id INTEGER PRIMARY KEY AUTOINCREMENT, PlayerId INTEGER,\
            FOREIGN KEY(PlayerId) REFERENCES Players(Id) ON DELETE CASCADE);")

        cur.execute("CREATE TABLE IF NOT EXISTS Timers(Id INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT, \
                Duration INTEGER, Time DATETIME)")

        cur.execute("CREATE TABLE IF NOT EXISTS Users(Id INTEGER PRIMARY KEY AUTOINCREMENT, Email TEXT NOT NULL, Password TEXT NOT NULL,\
            UNIQUE(Email));")

        cur.execute("CREATE TABLE IF NOT EXISTS Admins(Id INTEGER PRIMARY KEY NOT NULL,\
            FOREIGN KEY(Id) REFERENCES Users(Id) ON DELETE CASCADE);")

        cur.execute("CREATE TABLE IF NOT EXISTS ResetLinks(Id CHAR(32) PRIMARY KEY NOT NULL, User INTEGER, Expires DATETIME,\
            FOREIGN KEY(User) REFERENCES Users(Id));")

        cur.execute("CREATE TABLE IF NOT EXISTS VerifyLinks(Id CHAR(32) PRIMARY KEY NOT NULL, Email TEXT NOT NULL, Expires DATETIME);")

        cur.execute("CREATE TABLE IF NOT EXISTS Quarters(Quarter TEXT NOT NULL, GameCount INTEGER NOT NULL);")

        cur.execute("CREATE TABLE IF NOT EXISTS Settings(UserId INTEGER, Setting TEXT NOT NULL, Value SETTING NOT NULL, \
            FOREIGN KEY(UserId) REFERENCES Users(Id));")

def addGame(scores, gamedate = None, gameid = None):
    if gamedate is None:
        gamedate = datetime.datetime.now().strftime("%Y-%m-%d")

    if scores is None:
        return {"status":1, "error":"Please enter some scores"}

    if len(scores) != 4 and len(scores) != 5:
        return {"status":1, "error":"Please enter 4 or 5 scores"}

    total = 0
    for score in scores:
        total += score['score']

        if score['player'] == "":
            return {"status":1, "error":"Please enter all player names"}

    if total != len(scores) * 25000:
        return {"status":1, "error":"Scores do not add up to " + len(scores) * 25000}

    scores.sort(key=lambda x: x['score'], reverse=True)

    with getCur() as cur:
        if gameid is None:
            cur.execute("SELECT GameId FROM Scores ORDER BY GameId DESC LIMIT 1")
            row = cur.fetchone()
            if row is not None:
                gameid = row[0] + 1
            else:
                gameid = 0
        else:
            cur.execute("DELETE FROM Scores WHERE GameId = ?", (gameid,))

        for i in range(0, len(scores)):
            score = scores[i]

            cur.execute("SELECT Id FROM Players WHERE Id = ? OR Name = ?", (score['player'], score['player']))
            player = cur.fetchone()
            if player is None or len(player) == 0:
                cur.execute("INSERT INTO Players(Name) VALUES(?)", (score['player'],))
                cur.execute("SELECT Id FROM Players WHERE Name = ?", (score['player'],))
                player = cur.fetchone()
            player = player[0]

            adjscore = util.getScore(score['score'], len(scores), i + 1) - score['chombos'] * 8
            cur.execute("INSERT INTO Scores(GameId, PlayerId, Rank, PlayerCount, RawScore, Chombos, Score, Date, Quarter) VALUES(?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y', ?) || ' ' || case ((strftime('%m', ?) - 1) / 3) when 0 then '1st' when 1 then '2nd' when 2 then '3rd' when 3 then '4th' end)", (gameid, player, i + 1, len(scores), score['score'], score['chombos'], adjscore, gamedate, gamedate, gamedate))
    return {"status":0}
