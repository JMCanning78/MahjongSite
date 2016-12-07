#!/usr/bin/env python3

import json
from flask import render_template, session, request, Response

import util
import db
import settings

from MahjongSite import app

@app.route('/')
def MainPage():
    admin = 'admin' in session and session['admin']
    return render_template("index.html", admin = admin)

@app.route('/addgame', methods=["GET", "POST"])
def AddGame():
    if request.method == "GET":
        return render_template("addgame.html")
    elif request.method == "POST":
        scores = request.form['scores']
        if scores is None:
            return Response('{"status":1, "error":"Please enter some scores"}', mimetype = 'application/json')

        scores = json.loads(scores)

        if len(scores) != 4 and len(scores) != 5:
            return Response('{"status":1, "error":"Please enter some scores"}', mimetype = 'application/json')

        total = 0
        for score in scores:
            total += score['score']
        if total != len(scores) * 25000:
            return Response('{"status":1, "error":' + "Scores do not add up to " + len(scores) * 25000 + '}', mimetype = 'application/json')

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
                    return Response('{"status":1, "error":"Please enter all player names"}', mimetype = 'application/json')

                cur.execute("SELECT Id FROM Players WHERE Id = ? OR Name = ?", (score['player'], score['player']))
                player = cur.fetchone()
                if player is None or len(player) == 0:
                    cur.execute("INSERT INTO Players(Name) VALUES(?)", (score['player'],))
                    cur.execute("SELECT Id FROM Players WHERE Name = ?", (score['player'],))
                    player = cur.fetchone()
                player = player[0]

                adjscore = util.getScore(score['newscore'], len(scores), i + 1)
                cur.execute("INSERT INTO Scores(GameId, PlayerId, Rank, PlayerCount, RawScore, Chombos, Score, Date) VALUES(?, ?, ?, ?, ?, ?, ?, date('now', 'localtime'))", (gameid, player, i + 1, len(scores), score['score'], score['chombos'], adjscore))
            return Response('{"status":0}', mimetype = 'application/json')

@app.route('/pointcalculator')
def PointCalculator():
    return render_template("pointcalculator.html")

#    if len(sys.argv) > 1:
#        try:
#            socket = int(sys.argv[1])
#        except:
#            socket = sys.argv[1]
#    else:
#        socket = "/tmp/mahjong.sock"
#
#    if hasattr(settings, 'EMAILSERVER'):
#        qm = QueMail.get_instance()
#        qm.init(settings.EMAILSERVER, settings.EMAILUSER, settings.EMAILPASSWORD, settings.EMAILPORT, True)
#        qm.start()
#
#    tornado.options.parse_command_line()
#    http_server = tornado.httpserver.HTTPServer(Application(), max_buffer_size=24*1024**3)
#    if isinstance(socket, int):
#        http_server.add_sockets(tornado.netutil.bind_sockets(socket))
#    else:
#        http_server.add_socket(tornado.netutil.bind_unix_socket(socket))
#
#    signal.signal(signal.SIGINT, sigint_handler)
#
#    tornado.ioloop.PeriodicCallback(db.periodicCleanup, 60 * 60 * 1000).start() # run periodicCleanup once an hour
#    # start it up
#    tornado.ioloop.IOLoop.instance().start()
#
#    if qm is not None:
#        qm.end()
