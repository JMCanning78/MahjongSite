#!/usr/bin/env python3

import json
import db
import handler
from util import *

class PlayerStatsDataHandler(handler.BaseHandler):
    def get(self, player):
        with db.getCur() as cur:
            name = player
            cur.execute("SELECT Id,Name,MeetupName FROM Players WHERE Id = ? OR Name = ?", (player, player))
            player = cur.fetchone()
            if player is None or len(player) == 0:
                self.write(json.dumps({'status': 1,
                                       'error': "Couldn't find player"}))
                return
            playerID, name, meetupName = player
            statquery = """SELECT Max(Score),MIN(Score),COUNT(*),
               ROUND(SUM(Score) * 1.0/COUNT(*) * 100) / 100,
               ROUND(SUM(Rank) * 1.0/COUNT(*) * 100) / 100,
               MIN(Rank), MAX(Rank), MIN(Date), MAX(Date), 
               MIN(Quarter), MAX(Quarter)
               """
            fields = ['maxscore', 'minscore', 'numgames', 'avgscore',
                      'avgrank', 'maxrank', 'minrank', 'mindate', 'maxdate',
                      'minquarter', 'maxquarter']
            N = 5
            periods = [
                {'name': 'All Time Stats',
                 'subquery': "FROM Scores WHERE PlayerId = ?",
                 'params': (playerID,)
                },
            ]
            p = periods[0]
            cur.execute(statquery + p['subquery'], p['params'])
            p.update(dict(zip(fields,
                              map(lambda x: round(x, 2) if isinstance(x, float) else x,
                                  cur.fetchone()))))
            if p['numgames'] == 0:
                return self.render("playerstats.html", name=name,
                                   error = "Couldn't find any scores for")
            
            # Add optional periods if warranted
            if p['numgames'] > N:
                periods.append(
                    {'name': 'Last {0} Game Stats'.format(N),
                     'subquery': "FROM (SELECT * FROM Scores WHERE PlayerId = ? ORDER BY Date DESC LIMIT ?)",
                     'params': (playerID, N)
                     })
            if p['minquarter'] < p['maxquarter']:
                periods.append(
                    {'name': 'Quarter {0} Stats'.format(p['maxquarter']),
                     'subquery': "FROM Scores WHERE PlayerId = ? AND Quarter = ?",
                     'params': (playerID, p['maxquarter'])
                     })
                prevQtr = formatQuarter(prevQuarter(parseQuarter(p['maxquarter'])))
                periods.append(
                    {'name': 'Quarter {0} Stats'.format(prevQtr),
                     'subquery': "FROM Scores WHERE PlayerId = ? AND Quarter = ?",
                     'params': (playerID, prevQtr)
                     })
            for p in periods[1:]:
                cur.execute(statquery + p['subquery'], p['params'])
                p.update(dict(zip(fields,
                                  map(lambda x: round(x, 2) if isinstance(x, float) else x,
                                      cur.fetchone()))))
            self.write(json.dumps({'playerstats': periods}))

        
class PlayerStatsHandler(handler.BaseHandler):
    def get(self, player):
        with db.getCur() as cur:
            name = player
            cur.execute("SELECT Id,Name,MeetupName FROM Players WHERE Id = ? OR Name = ?", (player, player))
            player = cur.fetchone()
            if player is None or len(player) == 0:
                return self.render("playerstats.html", name=name,
                                   error = "Couldn't find player")

            player, name, meetupname = player
            self.render("playerstats.html",
                        error = None,
                        name = name,
                        meetupname = meetupname,
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
