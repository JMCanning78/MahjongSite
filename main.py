#!/usr/bin/env python3

import sys
import os.path
import os
import math
import tornado.httpserver
from tornado.httpclient import AsyncHTTPClient
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.template
import signal
import json
import datetime

import db

import seating

# import and define tornado-y things
from tornado.options import define, options
define("port", default=5000, type=int)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class AddGameHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("addgame.html")
    def post(self):
        scores = self.get_argument('scores', None)
        if scores is None:
            self.write('{"status":1, "error":"Please enter some scores"}')
            return

        scores = json.loads(scores)

        if len(scores) != 4 and len(scores) != 5:
            self.write('{"status":1, "error":"Please enter same scores"}')
            return

        total = 0
        for score in scores:
            total += score['score']
        if total != len(scores) * 25000:
            self.write('{"status":1, "error":' + "Scores do not add up to " + len(scores) * 25000 + '}')
            return

        with db.getCur() as cur:
            gameid = None
            for i in range(0, len(scores)):
                score = scores[i]
                if gameid == None:
                    cur.execute("SELECT GameId FROM Scores ORDER BY GameId DESC LIMIT 1")
                    gameid = cur.fetchone()[0] + 1

                if score['player'] == "":
                    self.write('{"status":1, "error":"Please enter all player names"}')
                    return

                cur.execute("SELECT Id FROM Players WHERE Id = ? OR Name = ?", (score['player'], score['player']))
                player = cur.fetchone()
                if player is None or len(player) == 0:
                    cur.execute("INSERT INTO Players(Name) VALUES(?)", (score['player'],))
                    cur.execute("SELECT Id FROM Players WHERE Name = ?", (score['player'],))
                    player = cur.fetchone()
                player = player[0]

                adjscore = getScore(score['score'], len(scores), i + 1)
                cur.execute("INSERT INTO Scores(GameId, PlayerId, Rank, PlayerCount, RawScore, Score, Date) VALUES(?, ?, ?, ?, ?, ?, date('now'))", (gameid, player, i + 1, len(scores), score['score'], adjscore))
            self.write('{"status":0}')

def getScore(score, numplayers, rank):
    uma = (3 - rank) * 10
    if numplayers == 5:
        uma += 5
    return score / 1000.0 - 30 + uma

class LeaderboardHandler(tornado.web.RequestHandler):
    def get(self):
        with db.getCur() as cur:
            leaderboards = {}
            cur.execute("SELECT strftime('%Y', Scores.Date), Players.Name, ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) / 100 AS AvgScore, COUNT(Scores.Score) AS GameCount FROM Players LEFT JOIN Scores ON Players.Id = Scores.PlayerId GROUP BY strftime('%Y', Date),Players.Id HAVING GameCount >= 4 ORDER BY AvgScore DESC;")
            rows = cur.fetchall()
            places={}
            for row in rows:
                if row[0] not in leaderboards:
                    leaderboards[row[0]] = []
                    places[row[0]] = 1
                leaderboard = leaderboards[row[0]]
                leaderboard += [[places[row[0]], row[1], row[2], row[3]]]
                places[row[0]] += 1
            self.render("leaderboard.html", leaderboards=sorted(list(leaderboards.items()), reverse=True))

class HistoryHandler(tornado.web.RequestHandler):
    def get(self, page):
        if page is None:
            page = 0
        else:
            page = int(page[1:]) - 1
        PERPAGE = 5
        with db.getCur() as cur:
            cur.execute("SELECT DISTINCT Date FROM Scores ORDER BY Date DESC")
            dates = cur.fetchall()
            gamecount = len(dates)
            cur.execute("SELECT Scores.GameId, strftime('%Y-%m-%d', Scores.Date), Rank, Players.Name, Scores.RawScore, Scores.Score FROM Scores INNER JOIN Players ON Players.Id = Scores.PlayerId WHERE Scores.Date BETWEEN ? AND ? GROUP BY Scores.Id ORDER BY Scores.Date ASC;", (dates[min(page * PERPAGE + PERPAGE - 1, gamecount - 1)][0], dates[min(page * PERPAGE, gamecount - 1)][0]))
            rows = cur.fetchall()
            games = {}
            for row in rows:
                if row[0] not in games:
                    games[row[0]] = {'date':row[1], 'scores':{}}
                games[row[0]]['scores'][row[2]] = (row[3], row[4], row[5])
            pages = range(max(1, page + 1 - 10), min(int(math.ceil(gamecount * 1.0 / PERPAGE) + 1), page + 1 + 10))
            games = sorted(games.values(), key=lambda x: x["date"], reverse=True)
            if page != 0:
                prev = page
            else:
                prev = None
            if page + 1 < gamecount / PERPAGE + 1:
                nex = page + 2
            else:
                nex = None
            self.render("history.html", games=games, curpage=page + 1, pages=pages, gamecount=gamecount, nex = nex, prev = prev)

class PlayerStats(tornado.web.RequestHandler):
    def get(self, player):
        with db.getCur() as cur:
            cur.execute("SELECT Id,Name FROM Players WHERE Id = ? OR Name = ?", (player, player))
            player = cur.fetchone()
            if len(player) == 0:
                self.render("stats.html", error="Couldn't find that player")
                return
            name = player[1]
            player = player[0]
            cur.execute("SELECT Max(Score),MIN(Score),COUNT(*),ROUND(SUM(Score) * 1.0/COUNT(*) * 100) / 100,ROUND(SUM(Rank) * 1.0/COUNT(*) * 100) / 100 FROM Scores WHERE PlayerId = ?", (player,))
            row = cur.fetchone()
            maxscore = row[0]
            minscore = row[1]
            numgames = row[2]
            avgscore = row[3]
            avgrank = row[4]
            cur.execute("SELECT ROUND(Sum(Score) * 1.0 / COUNT(*) * 100) / 100, ROUND(Sum(Rank) * 1.0 / COUNT(*) * 100) / 100 FROM (SELECT * FROM Scores WHERE PlayerId = ? ORDER BY Date DESC LIMIT 5)", (player,))
            row = cur.fetchone()
            avgscore5 = row[0]
            avgrank5 = row[1]
            self.render("stats.html",
                    error = None,
                    name = name,
                    maxscore = maxscore,
                    minscore = minscore,
                    numgames = numgames,
                    avgscore = avgscore,
                    avgrank  = avgrank,
                    avgscore5 = avgscore5,
                    avgrank5 = avgrank5
                )

class PointCalculator(tornado.web.RequestHandler):
    def get(self):
        self.render("pointcalculator.html")

class Application(tornado.web.Application):
    def __init__(self):
        db.init()

        handlers = [
                (r"/", MainHandler),
                (r"/addgame", AddGameHandler),
                (r"/leaderboard", LeaderboardHandler),
                (r"/history(/[0-9]+)?", HistoryHandler),
                (r"/playerstats/(.*)", PlayerStats),
                (r"/seating", seating.SeatingHandler),
                (r"/seating/regentables", seating.RegenTables),
                (r"/seating/clearcurrentplayers", seating.ClearCurrentPlayers),
                (r"/seating/addcurrentplayer", seating.AddCurrentPlayer),
                (r"/seating/removeplayer", seating.RemovePlayer),
                (r"/seating/currentplayers.json", seating.CurrentPlayers),
                (r"/seating/currenttables.json", seating.CurrentTables),
                (r"/seating/players.json", seating.PlayersList),
                (r"/pointcalculator", PointCalculator),
        ]
        settings = dict(
                template_path = os.path.join(os.path.dirname(__file__), "templates"),
                static_path = os.path.join(os.path.dirname(__file__), "static"),
                debug = True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            port = 5000
    else:
        port = 5000

    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), max_buffer_size=24*1024**3)
    http_server.listen(os.environ.get("PORT", port))

    signal.signal(signal.SIGINT, sigint_handler)

    # start it up
    tornado.ioloop.IOLoop.instance().start()
    qm.end()


def sigint_handler(signum, frame):
    tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    main()
