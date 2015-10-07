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

import db

import seating

# import and define tornado-y things
from tornado.options import define, options
define("port", default=5000, type=int)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class PointCalculator(tornado.web.RequestHandler):
    def get(self):
        self.render("pointcalculator.html")

class Application(tornado.web.Application):
    def __init__(self):
        db.init()

        handlers = [
                (r"/", MainHandler),
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
