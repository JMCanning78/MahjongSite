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

from quemail import QueMail
import handler
import util
import db
import settings

import seating
import login
import admin

# import and define tornado-y things
from tornado.options import define, options
cookie_secret = util.randString(32)

class MainHandler(handler.BaseHandler):
    def get(self):
        admin = self.get_secure_cookie("admin")
        self.render("index.html", admin = admin)

class AddGameHandler(handler.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("addgame.html")
    @tornado.web.authenticated
    def post(self):
        scores = self.get_argument('scores', None)
        if scores is None:
            self.write('{"status":1, "error":"Please enter some scores"}')
            return

        scores = json.loads(scores)

        if len(scores) != 4 and len(scores) != 5:
            self.write('{"status":1, "error":"Please enter some scores"}')
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
                    row = cur.fetchone()
                    if row is not None:
                        gameid = row[0] + 1
                    else:
                        gameid = 0

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

                adjscore = getScore(score['newscore'], len(scores), i + 1)
                cur.execute("INSERT INTO Scores(GameId, PlayerId, Rank, PlayerCount, RawScore, Chombos, Score, Date) VALUES(?, ?, ?, ?, ?, ?, ?, date('now', 'localtime'))", (gameid, player, i + 1, len(scores), score['score'], score['chombos'], adjscore))
            self.write('{"status":0}')

def getScore(score, numplayers, rank):
    umas = {4:[15,5,-5,-15],
            5:[15,5,0,-5,-15]}
    return score / 1000.0 - 25 + umas[numplayers][rank - 1]

class LeaderboardHandler(handler.BaseHandler):
    def get(self, period):
        self.render("leaderboard.html")

class LeaderDataHandler(handler.BaseHandler):
    def get(self, period):
        if len(period) > 0:
            period = period[1:]
        with db.getCur() as cur:
            leaderboards = {}
            queries = {
                    "annual":[
                        """SELECT strftime('%Y', Scores.Date), Players.Name, ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) / 100 AS AvgScore, COUNT(Scores.Score) AS GameCount, 0
                            FROM Players LEFT JOIN Scores ON Players.Id = Scores.PlayerId
                            GROUP BY strftime('%Y', Date),Players.Id
                            HAVING GameCount >= 4 AND GameCount <= 8 ORDER BY AvgScore DESC;""",
                        """SELECT strftime('%Y', Scores.Date), Players.Name, ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) / 100 AS AvgScore, COUNT(Scores.Score) + 1 AS GameCount, 1
                            FROM Players LEFT JOIN Scores ON Players.Id = Scores.PlayerId
                            WHERE Scores.Id NOT IN (SELECT Id FROM Scores GROUP BY PlayerId,strftime('%Y', Date) HAVING Score = MIN(Score))
                            GROUP BY strftime('%Y', Date),Players.Id
                            HAVING GameCount > 8 ORDER BY AvgScore DESC;"""
                    ],
                    "biannual":[
                        """SELECT strftime('%Y', Scores.Date) || ' ' || case ((strftime('%m', Date) - 1) / 6) when 0 then '1st' when 1 then '2nd' end,
                                Players.Name, ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) / 100 AS AvgScore, COUNT(Scores.Score) AS GameCount, 0
                            FROM Players LEFT JOIN Scores ON Players.Id = Scores.PlayerId
                            GROUP BY strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 6),Players.Id
                            HAVING GameCount >= 4 AND GameCount <= 8 ORDER BY AvgScore DESC;""",
                        """SELECT strftime('%Y', Scores.Date) || ' ' || case ((strftime('%m', Date) - 1) / 6) when 0 then '1st' when 1 then '2nd' end,
                                Players.Name, ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) / 100 AS AvgScore, COUNT(Scores.Score) + 1 AS GameCount, 1
                            FROM Players LEFT JOIN Scores ON Players.Id = Scores.PlayerId
                            WHERE Scores.Id NOT IN (SELECT Id FROM Scores GROUP BY PlayerId,strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 6) HAVING Score = MIN(Score))
                            GROUP BY strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 6),Players.Id
                            HAVING GameCount > 8 ORDER BY AvgScore DESC;"""
                    ],
                    "quarter":[
                        """SELECT strftime('%Y', Scores.Date) || ' ' || case ((strftime('%m', Date) - 1) / 3) when 0 then '1st' when 1 then '2nd' when 2 then '3rd' when 3 then '4th' end,
                                Players.Name, ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) / 100 AS AvgScore, COUNT(Scores.Score) AS GameCount, 0
                            FROM Players LEFT JOIN Scores ON Players.Id = Scores.PlayerId
                            GROUP BY strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 3),Players.Id
                            HAVING GameCount <= 8 ORDER BY AvgScore DESC;""",
                        """SELECT strftime('%Y', Scores.Date) || ' ' || case ((strftime('%m', Date) - 1) / 3) when 0 then '1st' when 1 then '2nd' when 2 then '3rd' when 3 then '4th' end,
                                Players.Name, ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) / 100 AS AvgScore, COUNT(Scores.Score) + 1 AS GameCount, 1
                            FROM Players LEFT JOIN Scores ON Players.Id = Scores.PlayerId
                            WHERE Scores.Id NOT IN (SELECT Id FROM Scores GROUP BY PlayerId,strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 3) HAVING Score = MIN(Score))
                            GROUP BY strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 3),Players.Id
                            HAVING GameCount > 8 ORDER BY AvgScore DESC;"""
                    ]
            }
            if period not in queries:
                period = "quarter"
            cur.execute(queries[period][0])
            rows = cur.fetchall()
            cur.execute(queries[period][1])
            rows += cur.fetchall()
            places={}
            rows.sort(key=lambda row: row[2], reverse=True) # sort by score
            for row in rows:
                if row[0] not in leaderboards:
                    leaderboards[row[0]] = []
                    places[row[0]] = 1
                leaderboard = leaderboards[row[0]]
                leaderboard += [{'place': places[row[0]],
                                'name':row[1],
                                'score':row[2],
                                'count':row[3] if row[4] == 0 else str(row[3] - 1) + " (+1)",
                                'dropped':row[4]}]
                places[row[0]] += 1
            leaders = sorted(list(leaderboards.items()), reverse=True)
            leaderboards = []
            for name, scores in leaders:
                leaderboards += [{'name':name, 'scores':scores}]
            leaderboards={'leaderboards':leaderboards}
            self.write(json.dumps(leaderboards))

class HistoryHandler(handler.BaseHandler):
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
            cur.execute("SELECT Scores.GameId, strftime('%Y-%m-%d', Scores.Date), Rank, Players.Name, Scores.RawScore / 1000.0, Scores.Score, Scores.Chombos FROM Scores INNER JOIN Players ON Players.Id = Scores.PlayerId WHERE Scores.Date BETWEEN ? AND ? GROUP BY Scores.Id ORDER BY Scores.Date ASC;", (dates[min(page * PERPAGE + PERPAGE - 1, gamecount - 1)][0], dates[min(page * PERPAGE, gamecount - 1)][0]))
            rows = cur.fetchall()
            games = {}
            for row in rows:
                if row[0] not in games:
                    games[row[0]] = {'date':row[1], 'scores':{}}
                games[row[0]]['scores'][row[2]] = (row[3], row[4], round(row[5], 2), row[6])
            maxpage = math.ceil(gamecount * 1.0 / PERPAGE + 1)
            pages = range(max(1, page + 1 - 10), int(min(maxpage, page + 1 + 10) + 1))
            games = sorted(games.values(), key=lambda x: x["date"], reverse=True)
            if page != 0:
                prev = page
            else:
                prev = None
            if page + 1 < maxpage:
                nex = page + 2
            else:
                nex = None
            self.render("history.html", games=games, curpage=page + 1, pages=pages, gamecount=gamecount, nex = nex, prev = prev)

class PlayerStats(handler.BaseHandler):
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

class PointCalculator(handler.BaseHandler):
    def get(self):
        self.render("pointcalculator.html")

class Application(tornado.web.Application):
    def __init__(self):
        db.init()

        handlers = [
                (r"/", MainHandler),
                (r"/login", login.LoginHandler),
                (r"/logout", login.LogoutHandler),
                (r"/invite", login.InviteHandler),
                (r"/verify/([^/]+)", login.VerifyHandler),
                (r"/reset", login.ResetPasswordHandler),
                (r"/reset/([^/]+)", login.ResetPasswordLinkHandler),
                (r"/addgame", AddGameHandler),
                (r"/leaderboard(/[^/]*)?", LeaderboardHandler),
                (r"/leaderdata(/[^/]*)?", LeaderDataHandler),
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
                (r"/admin", admin.AdminPanelHandler),
                (r"/admin/users", admin.ManageUsersHandler),
                (r"/admin/promote/([0-9]*)", admin.PromoteUserHandler),
                (r"/admin/demote/([0-9]*)", admin.DemoteUserHandler),
        ]
        settings = dict(
                template_path = os.path.join(os.path.dirname(__file__), "templates"),
                static_path = os.path.join(os.path.dirname(__file__), "static"),
                debug = True,
                cookie_secret = cookie_secret,
                login_url = "/login"
        )
        tornado.web.Application.__init__(self, handlers, **settings)

def periodicCleanup():
    with db.getCur() as cur:
        cur.execute("DELETE FROM VerifyLinks WHERE Expires <= NOW()")

def main():
    if len(sys.argv) > 1:
        try:
            socket = int(sys.argv[1])
        except:
            socket = sys.argv[1]
    else:
        socket = "/tmp/mahjong.sock"

    if hasattr(settings, 'EMAILSERVER'):
        qm = QueMail.get_instance()
        qm.init(settings.EMAILSERVER, settings.EMAILUSER, settings.EMAILPASSWORD, settings.EMAILPORT, True)
        qm.start()

    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), max_buffer_size=24*1024**3)
    if isinstance(socket, int):
        http_server.add_sockets(tornado.netutil.bind_sockets(socket))
    else:
        http_server.add_socket(tornado.netutil.bind_unix_socket(socket))

    signal.signal(signal.SIGINT, sigint_handler)

    tornado.ioloop.PeriodicCallback(periodicCleanup, 60 * 60 * 1000).start() # run periodicCleanup once an hour
    # start it up
    tornado.ioloop.IOLoop.instance().start()
    qm.end()


def sigint_handler(signum, frame):
    tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    main()
