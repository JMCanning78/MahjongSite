#!/usr/bin/env python3

import json

import handler
import db
import settings

import scores

class RatingsHandler(handler.BaseHandler):
    def get(self):
        self.render("ratings.html")

class RatingsDataHandler(handler.BaseHandler):
    def get(self):
        columns = ["name", "rating", "count"]
        query = """SELECT
            Players.Name,
            ROUND((SUM(Scores.DeltaRating) + {DEFAULT_RATING}) * 100) / 100 AS Rating,
            COUNT(*) AS GameCount
          FROM Scores LEFT JOIN Players ON Players.Id = Scores.PlayerId
          WHERE Players.Id != ?
          GROUP BY Players.Id
          ORDER BY Rating DESC;""".format(DEFAULT_RATING=settings.DEFAULT_RATING)
        with db.getCur() as cur:
            cur.execute(query, (scores.getUnusedPointsPlayerID(),))
            players = [dict(zip(columns, row)) for row in cur.fetchall()]
        self.write(json.dumps({'players':players}))
