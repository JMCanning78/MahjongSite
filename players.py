#!/usr/bin/env python3

import datetime
import collections

import handler
import db
import settings
import scores

class PlayersHandler(handler.BaseHandler):
    def get(self):
        with db.getCur() as cur:
            playerFields = db.table_field_names('Players')
            cur.execute(("SELECT {}, QuarterId FROM Players"
                         " LEFT OUTER JOIN Memberships"
                         " ON Players.Id = Memberships.PlayerId"
                         " WHERE Id != ?"
                         " ORDER BY Name ASC, QuarterId ASC").format(
                             ', '.join(playerFields)),
                        (scores.getUnusedPointsPlayerID(),))
            rows = cur.fetchall()
            players = collections.OrderedDict({})
            last_player = None
            for row in rows:          # Build dictionary for each player
                if row[0] != last_player:
                    players[row[0]] = collections.defaultdict(
                        lambda: list(),
                        zip(playerFields, row))
                    last_player = row[0]
                memberQtr = row[len(playerFields)]
                if memberQtr is not None:  # Memberships is a list of qtrs
                    players[row[0]]['Memberships'].append(memberQtr)

            cur.execute("SELECT DISTINCT Quarter FROM Scores UNION"
                        " SELECT DISTINCT Quarter FROM Quarters"
                        " ORDER BY Quarter ASC")
            quarters = [row[0] for row in cur.fetchall()]
            initialQtrsShown = [scores.quarterString()]
            if initialQtrsShown[0] in quarters:
                index = quarters.index(initialQtrsShown[0])
                initialQtrsShown = quarters[index:
                                            index + settings.MEMBERSHIPQUARTERS]
            elif len(quarters) > 0:
                initialQtrsShown = quarters[- settings.MEMBERSHIPQUARTERS:]
            else:
                initialQtrsShown = []

        self.render("players.html",
                    message = "No players found" if len(rows) == 0 else "",
                    players=players, quarters=quarters,
                    visibleQtrs=initialQtrsShown)

