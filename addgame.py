#!/usr/bin/env python3

import json
import db
import handler
import tornado.web
import settings

class AddGameHandler(handler.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("addgame.html", 
                    unusedPointsIncrement=scores.unusedPointsIncrement(),
                    fourplayertotal='{:,d}'.format(4 * settings.SCOREPERPLAYER))
    @tornado.web.authenticated
    def post(self):
        scores = self.get_argument('scores', None)

        scores = json.loads(scores)

        self.write(json.dumps(db.addGame(scores)))
