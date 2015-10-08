#!/usr/bin/env python2.7

import sys
import os.path
import os
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

        print scores
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

        adjscores = [0] * len(scores)
        currentscore = 0
        for i in range(0, len(scores)):
            s = getScore(scores[i]['score'], len(scores), i)
            currentscore += s
            if i == len(scores):
                if currentscore < 0:
                    adjscores[0] -= currentscore
                elif currentscore > 0:
                    s -= currentscore
            adjscores[i] = s


        with db.getCur() as cur:
            gameid = None
            for i in range(0, len(scores)):
                if gameid == None:
                    cur.execute("SELECT GameId FROM Scores ORDER BY GameId DESC LIMIT 1")
                    gameid = cur.fetchone()[0] + 1

                cur.execute("SELECT Id FROM Players WHERE Id = ? OR Name = ?", (score['player'], score['player']))
                player = cur.fetchone()
                if len(player) == 0:
                    self.write('{"status":1, "error":"Player ' + score['player'] + 'not found"}')
                    return
                player = player[0]
                print player

                cur.execute("INSERT INTO Scores(GameId, PlayerId, Rank, PlayerCount, RawScore, Score, Date) VALUES(?, ?, ?, ?, ?, ?, date('now'))", (gameid, player, i + 1, len(scores), score['score'], adjscores[i]))
            self.write('{"status":0}')

def getScore(score, numplayers, rank):
    uma = (3 - rank) * 10
    if numplayers == 5:
        uma += 5
    return round(score, -3) / 1000 - 30 + uma

class LeaderboardHandler(tornado.web.RequestHandler):
    def get(self):
        with db.getCur() as cur:
            cur.execute("SELECT Players.Name, ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) / 100 AS AvgScore, COUNT(Scores.Score) AS GameCount FROM Players LEFT JOIN Scores ON Players.Id = Scores.PlayerId GROUP BY Players.Id HAVING GameCount > 4 ORDER BY AvgScore DESC;")
            rows = cur.fetchall()
            place=1
            leaderboard = []
            for row in rows:
                leaderboard += [[place, row[0], row[1], row[2]]]
                place += 1
            self.render("leaderboard.html", leaderboard=leaderboard)

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
            cur.execute("SELECT ROUND(Sum(Score) * 1.0 / COUNT(*) * 100) / 100, ROUND(Sum(Rank) * 1.0 / COUNT(*) * 100) / 100 FROM (SELECT * FROM Scores WHERE PlayerId = ? ORDER BY Date LIMIT 5)", (player,))
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
