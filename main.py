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
import leaderboard
import playerstats

# import and define tornado-y things
from tornado.options import define, options
cookie_secret = util.randString(32)

class MainHandler(handler.BaseHandler):
    def get(self):
        admin = handler.stringify(self.get_secure_cookie("admin"))

        no_user = False
        with db.getCur() as cur:
            cur.execute("SELECT COUNT(*) FROM Users")
            no_user = cur.fetchone()[0] == 0

        self.render("index.html", admin = admin, no_user = no_user)

class AddGameHandler(handler.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("addgame.html")
    @tornado.web.authenticated
    def post(self):
        scores = self.get_argument('scores', None)

        scores = json.loads(scores)

        self.write(json.dumps(db.addGame(scores)))

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
            if gamecount > 0:
                cur.execute("SELECT Scores.GameId, strftime('%Y-%m-%d', Scores.Date), Rank, Players.Name, Scores.RawScore / 1000.0, Scores.Score, Scores.Chombos FROM Scores INNER JOIN Players ON Players.Id = Scores.PlayerId WHERE Scores.Date BETWEEN ? AND ? GROUP BY Scores.Id ORDER BY Scores.Date ASC;", (dates[min(page * PERPAGE + PERPAGE - 1, gamecount - 1)][0], dates[min(page * PERPAGE, gamecount - 1)][0]))
                rows = cur.fetchall()
                games = {}
                for row in rows:
                    if row[0] not in games:
                        games[row[0]] = {'date':row[1], 'scores':{}, 'id':row[0]}
                    games[row[0]]['scores'][row[2]] = (row[3], row[4], round(row[5], 2), row[6])
                maxpage = math.ceil(gamecount * 1.0 / PERPAGE)
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
                self.render("history.html", error=None, games=games, curpage=page + 1, pages=pages, gamecount=gamecount, nex = nex, prev = prev)
            else:
                self.render("message.html", message="No games entered thusfar", title="Game History")

class PlayerHistory(handler.BaseHandler):
    def get(self, player, page):
        if page is None:
            page = 0
        else:
            page = int(page[1:]) - 1
        PERPAGE = 10
        with db.getCur() as cur:
            cur.execute("SELECT Id,Name FROM Players WHERE Id = ? OR Name = ?", (player, player))
            player = cur.fetchone()
            if len(player) == 0:
                self.render("message.html", message="Couldn't find that player", title="User Game History")
                return
            name = player[1]
            player = player[0]
            cur.execute("SELECT DISTINCT GameId FROM Scores WHERE PlayerId = ? ORDER BY Date DESC", (player,))
            games = [i[0] for i in cur.fetchall()]
            gamecount = len(games)
            if gamecount > 0:
                thesegames = games[min(page * PERPAGE, gamecount - 1):min(page * PERPAGE + PERPAGE, gamecount)]
                placeholder= '?' # For SQLite. See DBAPI paramstyle
                placeholders= ', '.join(placeholder for i in range(len(thesegames)))
                cur.execute("SELECT Scores.GameId, strftime('%Y-%m-%d', Scores.Date), Rank, Players.Name, Scores.RawScore / 1000.0, Scores.Score, Scores.Chombos FROM Scores INNER JOIN Players ON Players.Id = Scores.PlayerId WHERE Scores.GameId IN (" + placeholders + ") GROUP BY Scores.Id ORDER BY Scores.Date ASC;", thesegames)
                rows = cur.fetchall()
                games = {}
                for row in rows:
                    if row[0] not in games:
                        games[row[0]] = {'date':row[1], 'scores':{}, 'id':row[0]}
                    games[row[0]]['scores'][row[2]] = (row[3], row[4], round(row[5], 2), row[6])
                maxpage = math.ceil(gamecount * 1.0 / PERPAGE)
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
                self.render("userhistory.html",
                        error=None,
                        games=games,
                        curpage=page + 1,
                        pages=pages,
                        gamecount=gamecount,
                        nex = nex,
                        prev = prev,
                        user = name,
                        player = player)
            else:
                self.render("message.html", message="No games entered thusfar", title="Game History", user = name)

class PointCalculator(handler.BaseHandler):
    def get(self):
        self.render("pointcalculator.html")

class Application(tornado.web.Application):
    def __init__(self):
        db.init()

        handlers = [
                (r"/", MainHandler),
                (r"/setup", login.SetupHandler),
                (r"/login", login.LoginHandler),
                (r"/logout", login.LogoutHandler),
                (r"/invite", login.InviteHandler),
                (r"/settings", login.SettingsHandler),
                (r"/verify/([^/]+)", login.VerifyHandler),
                (r"/reset", login.ResetPasswordHandler),
                (r"/reset/([^/]+)", login.ResetPasswordLinkHandler),
                (r"/addgame", AddGameHandler),
                (r"/leaderboard(/[^/]*)?", leaderboard.LeaderboardHandler),
                (r"/leaderdata(/[^/]*)?", leaderboard.LeaderDataHandler),
                (r"/history(/[0-9]+)?", HistoryHandler),
                (r"/playerhistory/(.*?)(/[0-9]+)?", PlayerHistory),
                (r"/playerstats/(.*)", playerstats.PlayerStats),
                (r"/seating", seating.SeatingHandler),
                (r"/seating/regentables", seating.RegenTables),
                (r"/seating/clearcurrentplayers", seating.ClearCurrentPlayers),
                (r"/seating/addcurrentplayer", seating.AddCurrentPlayer),
                (r"/seating/removeplayer", seating.RemovePlayer),
                (r"/seating/prioritizeplayer", seating.PrioritizePlayer),
                (r"/seating/currentplayers.json", seating.CurrentPlayers),
                (r"/seating/currenttables.json", seating.CurrentTables),
                (r"/seating/players.json", seating.PlayersList),
                (r"/seating/meetup", seating.AddMeetupPlayers),
                (r"/pointcalculator", PointCalculator),
                (r"/admin", admin.AdminPanelHandler),
                (r"/admin/users", admin.ManageUsersHandler),
                (r"/admin/addquarter", admin.AddQuarterHandler),
                (r"/admin/quarters", admin.QuartersHandler),
                (r"/admin/deletequarter/([^/]*)", admin.DeleteQuarterHandler),
                (r"/admin/delete/([0-9]*)", admin.DeleteGameHandler),
                (r"/admin/edit/([0-9]*)", admin.EditGameHandler),
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
        cur.execute("DELETE FROM VerifyLinks WHERE Expires <= datetime('now')")
        cur.execute("DELETE FROM Players WHERE Id NOT IN (SELECT PlayerId FROM Scores)")

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

    if qm is not None:
        qm.end()


def sigint_handler(signum, frame):
    tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    main()
