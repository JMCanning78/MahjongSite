#!/usr/bin/env python3

import db
import handler

class PlayerStats(handler.BaseHandler):
    def get(self, player):
        with db.getCur() as cur:
            name = player
            cur.execute("SELECT Id,Name,MeetupName FROM Players WHERE Id = ? OR Name = ?", (player, player))
            player = cur.fetchone()
            if player is None or len(player) == 0:
                return self.render("playerstats.html", name=name,
                                   error = "Couldn't find player")

            player, name, meetupname = player
            cur.execute("""SELECT Max(Score),MIN(Score),COUNT(*),
               ROUND(SUM(Score) * 1.0/COUNT(*) * 100) / 100,
               ROUND(SUM(Rank) * 1.0/COUNT(*) * 100) / 100,
               MIN(Date), Max(Date)
               FROM Scores WHERE PlayerId = ?""", (player,))
            maxscore, minscore, numgames, avgscore, avgrank, mindate, maxdate =\
                map(lambda x: round(x, 2) if isinstance(x, float) else x,
                    cur.fetchone())
            cur.execute("""
              SELECT ROUND(Sum(Score) * 1.0 / COUNT(*) * 100) / 100,
              ROUND(Sum(Rank) * 1.0 / COUNT(*) * 100) / 100
              FROM (SELECT * FROM Scores WHERE PlayerId = ?
                    ORDER BY Date DESC LIMIT 5)""", (player,))
            avgscore5, avgrank5 = cur.fetchone()
            self.render("playerstats.html",
                        error = None,
                        name = name,
                        meetupname = meetupname,
                        maxscore = maxscore,
                        minscore = minscore,
                        numgames = numgames,
                        avgscore = avgscore,
                        avgrank  = avgrank,
                        avgscore5 = avgscore5,
                        avgrank5 = avgrank5,
                        mindate = mindate,
                        maxdate = maxdate
                )
    def post(self, player):
        name = self.get_argument("name", player)
        meetupname = self.get_argument("meetupname", None)
        if name != player or meetupname is not None:
            args = []
            cols = []
            if name != player:
                cols += ["Name = ?"]
                args += [name]
            if meetupname is not None:
                cols += ["MeetupName = ?"]
                args += [meetupname]
            if len(args) > 0:
                query = "UPDATE Players SET " + ",".join(cols) + " WHERE Id = ? OR Name = ?"
                args += [player, player]
                with db.getCur() as cur:
                    cur.execute(query, args)
        self.redirect("/playerstats/" + name)
