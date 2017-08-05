#!/usr/bin/env python3

import json
import db
import handler
from util import *

class PlayerStatsDataHandler(handler.BaseHandler):
    _statquery = """
       SELECT Max(Score),MIN(Score),COUNT(*),
         ROUND(SUM(Score) * 1.0/COUNT(*) * 100) / 100,
         ROUND(SUM(Rank) * 1.0/COUNT(*) * 100) / 100,
         MIN(Rank), MAX(Rank), MIN(Date), MAX(Date), 
         MIN(Quarter), MAX(Quarter) {subquery} """
    _statqfields = ['maxscore', 'minscore', 'numgames', 'avgscore',
                    'avgrank', 'maxrank', 'minrank', 'mindate', 'maxdate',
                    'minquarter', 'maxquarter']
    _rankhistogramquery = """
        SELECT Rank, COUNT(*) {subquery} GROUP BY Rank ORDER BY Rank"""
    _rankhfields = ['rank', 'rankcount']
    
    def populate_queries(self, cur, period_dict):
        cur.execute(self._statquery.format(**period_dict),
                    period_dict['params'])
        period_dict.update(
            dict(zip(self._statqfields,
                     map(lambda x: round(x, 2) if isinstance(x, float) else x,
                         cur.fetchone()))))
        cur.execute(self._rankhistogramquery.format(**period_dict),
                    period_dict['params'])
        rank_histogram = dict([map(int, r) for r in cur.fetchall()])
        for i in range(1, 6):
            rank_histogram[i] = rank_histogram.get(i, 0)
        period_dict['rank_histogram'] = rank_histogram
        
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
            
            N = 5
            periods = [
                {'name': 'All Time Stats',
                 'subquery': "FROM Scores WHERE PlayerId = ?",
                 'params': (playerID,)
                },
            ]
            p = periods[0]
            self.populate_queries(cur, p)
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
                self.populate_queries(cur, p)

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
