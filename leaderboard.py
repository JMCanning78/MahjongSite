#!/usr/bin/env python3

import json
import memcache

import db
import handler
import settings
import scores

columns = ['Date', 'Name', 'AvgScore', 'GameCount', 'DropGames']
periods = {
    "annual":[
        """SELECT
             strftime('%Y', Scores.Date), Players.Name,
             ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100)
               / 100 AS AvgScore,
             COUNT(Scores.Score) AS GameCount,
             0
           FROM Scores LEFT JOIN Players ON Players.Id = Scores.PlayerId
           WHERE Players.Id != ?
           GROUP BY strftime('%Y', Date),Players.Id
           ORDER BY AvgScore DESC;"""
    ],
    "biannual":[
        """SELECT
             strftime('%Y', Scores.Date) || ' ' ||
               case ((strftime('%m', Date) - 1) / 6) when 0 then '1st'
                 when 1 then '2nd' end,
             Players.Name,
             ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100)
               / 100 AS AvgScore,
             COUNT(Scores.Score) AS GameCount,
             0
           FROM Scores LEFT JOIN Players ON Players.Id = Scores.PlayerId
           WHERE Players.Id != ?
        GROUP BY strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 6),Players.Id
        ORDER BY AvgScore DESC;"""
    ],
    "quarter":[
        """SELECT
             Scores.Quarter, Players.Name,
             ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100)
               / 100 AS AvgScore,
             COUNT(Scores.Score) AS GameCount,
             {DROPGAMES}
           FROM Scores
             LEFT JOIN Players ON Players.Id = Scores.PlayerId
             LEFT JOIN Quarters ON Scores.Quarter = Quarters.Quarter
           WHERE Players.Id != ? AND Scores.Id NOT IN
             (SELECT Id FROM Scores as s WHERE s.PlayerId = Scores.PlayerId AND s.Quarter = Scores.Quarter
                 ORDER BY s.Score ASC LIMIT {DROPGAMES})
           GROUP BY Scores.Quarter,Players.Id
           HAVING COUNT(Scores.Score) + {DROPGAMES} >= COALESCE(Quarters.GameCount,{DEFDROPGAMES}) * {DROPGAMES}
               AND COUNT(Scores.Score) + {DROPGAMES} < COALESCE(Quarters.GameCount,{DEFDROPGAMES}) * ({DROPGAMES} + 1)
           ORDER BY AvgScore DESC;""".format(DROPGAMES=i,DEFDROPGAMES=settings.DROPGAMES)
        for i in range(settings.MAXDROPGAMES)
    ]
}

class LeaderboardHandler(handler.BaseHandler):
    def get(self, period):
        self.render("leaderboard.html")

class LeaderDataHandler(handler.BaseHandler):
    def get(self, period):
        while period.startswith('/'):
            period = period[1:]
        if '/' in period:
            period, rest = period.split('/', 1)
        if period not in periods:
            period = "quarter"

        if settings.MEMCACHE != "":
            mc=memcache.Client([settings.MEMCACHE])
            leaderboards = mc.get("leaderboards_" + period)
        else:
            mc = None
            leaderboards = None

        if leaderboards is None:
            with db.getCur() as cur:
                leaderboards = {}
                rows = []
                for query in periods[period]:
                    cur.execute(query, (scores.getUnusedPointsPlayerID(),))
                    rows += [dict(zip(columns, row)) for row in cur.fetchall()]
                places={}
                last_place={}
                rows.sort(key=lambda row: row['AvgScore'], reverse=True) # sort by score
                for row in rows:
                    if row['Date'] not in leaderboards:
                        leaderboards[row['Date']] = []
                        places[row['Date']] = 1
                    leaderboard = leaderboards[row['Date']]
                    leaderboard += [
                        {'place': places[row['Date']],
                         'name':row['Name'],
                         'score':row['AvgScore'],
                         'count':str(row['GameCount']) + ("" if row['DropGames'] == 0 else " (+" + str(row['DropGames']) + ")"),
                         'dropped':row['DropGames']}]
                    places[row['Date']] += 1
                leaders = sorted(list(leaderboards.items()), reverse=True)
                leaderboards = []
                for name, leaderscores in leaders:
                    leaderboards += [{'name':name, 'scores':leaderscores}]
                leaderboards=json.dumps({'leaderboards':leaderboards})
                if mc is not None:
                    mc.set("leaderboards_" + period, leaderboards)
        self.write(leaderboards)

def clearCache():
    if settings.MEMCACHE != "":
        mc=memcache.Client([settings.MEMCACHE])
        mc.delete_multi(list(map(lambda period:"leaderboards_" + period, periods.keys())))
