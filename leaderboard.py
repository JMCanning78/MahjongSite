#!/usr/bin/env python3

import json
import db
import handler
import settings

class LeaderboardHandler(handler.BaseHandler):
    def get(self, period):
        self.render("leaderboard.html")

class LeaderDataHandler(handler.BaseHandler):
    def get(self, period, min_games='1', rank_visible=False):
        queries = {
            "annual":[
                """SELECT
                     strftime('%Y', Scores.Date), Players.Name,
                     ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) 
                       / 100 AS AvgScore,
                     COUNT(Scores.Score) AS GameCount, 0
                   FROM Scores LEFT JOIN Players ON Players.Id = Scores.PlayerId
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
                     COUNT(Scores.Score) AS GameCount, 0
                   FROM Scores LEFT JOIN Players ON Players.Id = Scores.PlayerId
                GROUP BY strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 6),Players.Id
                ORDER BY AvgScore DESC;"""
            ],
            "quarter":[
                """SELECT
                     Scores.Quarter, Players.Name,
                     ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100)
                       / 100 AS AvgScore,
                     COUNT(Scores.Score) AS GameCount, 0
                   FROM Scores LEFT JOIN Players ON Players.Id = Scores.PlayerId
                     LEFT JOIN Quarters ON Scores.Quarter = Quarters.Quarter
                   GROUP BY Scores.Quarter,Players.Id
                   HAVING COUNT(Scores.Score) < COALESCE(Quarters.GameCount, {0})
                   ORDER BY AvgScore DESC;""".format(settings.DROPGAMES),
                """SELECT
                     Scores.Quarter, Players.Name,
                     ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100)
                       / 100 AS AvgScore,
                     COUNT(Scores.Score) AS GameCount, 1
                   FROM Scores LEFT JOIN Players ON Players.Id = Scores.PlayerId
                     LEFT JOIN Quarters ON Scores.Quarter = Quarters.Quarter
                   WHERE Scores.Id NOT IN
                     (SELECT Id FROM Scores GROUP BY PlayerId, Scores.Quarter
                                            HAVING Score = MIN(Score))
                   GROUP BY Scores.Quarter,Players.Id
                   HAVING COUNT(Scores.Score) + 1 >= COALESCE(Quarters.GameCount,{0})
                   ORDER BY AvgScore DESC;""".format(settings.DROPGAMES),
            ]
        }
        while period.startswith('/'):
            period = period[1:]
        if '/' in period:
            period, rest = period.split('/', 1)
        if period not in queries:
            period = "quarter"
            
        if isinstance(min_games, int):
            min_games = str(min_games)
        elif min_games is None:
            min_games = '1'

        while min_games.startswith('/'):
            min_games = min_games[1:]
        if '/' in min_games:
            min_games, rest = min_games.split('/', 1)
        if not min_games.isdigit():
            min_games = '1'
            
        with db.getCur() as cur:
            leaderboards = {}
            rows = []
            for query in queries[period]:
                cur.execute(query)
                rows += cur.fetchall()
            places={}
            last_place={}
            rows.sort(key=lambda row: row[2], reverse=True) # sort by score
            for row in rows:
                if row[0] not in leaderboards:
                    leaderboards[row[0]] = []
                    places[row[0]] = 1
                    last_place[row[0]] = 0
                leaderboard = leaderboards[row[0]]
                if row[3] + row[4] >= int(min_games):
                    leaderboard += [
                        {'place': ("" if last_place[row[0]]+1 == places[row[0]]
                                   else "... ") + str(places[row[0]]),
                         'name':row[1],
                         'score':row[2],
                         'count':str(row[3]) + ("" if row[4] == 0 else " (+1)"),
                         'dropped':row[4]}]
                    last_place[row[0]] = places[row[0]]
                    places[row[0]] += 1
                elif not rank_visible:
                    places[row[0]] += 1
            leaders = sorted(list(leaderboards.items()), reverse=True)
            leaderboards = []
            for name, scores in leaders:
                leaderboards += [{'name':name, 'scores':scores}]
            leaderboards={'leaderboards':leaderboards}
            self.write(json.dumps(leaderboards))
