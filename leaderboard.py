#!/usr/bin/env python3

import json

import db
import handler
import settings
import scores

columns = ['Period', 'Date', 'PlayerId', 'AvgScore', 'GameCount', 'DropGames']
periods = {
    "annual":[
        """SELECT
            'annual',
             strftime('%Y', Scores.Date),
             PlayerId,
             ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100)
               / 100 AS AvgScore,
             COUNT(Scores.Score) AS GameCount,
             0
           FROM Scores
           WHERE PlayerId != ?
           GROUP BY strftime('%Y', Date),PlayerId
           ORDER BY AvgScore DESC;"""
    ],
    "biannual":[
        """SELECT
            'biannual',
             strftime('%Y', Scores.Date) || ' ' ||
               case ((strftime('%m', Date) - 1) / 6) when 0 then '1st'
                 when 1 then '2nd' end,
             PlayerId,
             ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100)
               / 100 AS AvgScore,
             COUNT(Scores.Score) AS GameCount,
             0
           FROM Scores
           WHERE PlayerId != ?
        GROUP BY strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 6),PlayerId
        ORDER BY AvgScore DESC;"""
    ],
    "quarter":[
        """SELECT
            'quarter',
             Scores.Quarter,
             PlayerId,
             ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100)
               / 100 AS AvgScore,
             COUNT(Scores.Score) AS GameCount,
             {DROPGAMES}
           FROM Scores
             LEFT JOIN Quarters ON Scores.Quarter = Quarters.Quarter
           WHERE PlayerId != ? AND Scores.Id NOT IN
             (SELECT Id FROM Scores as s WHERE s.PlayerId = Scores.PlayerId AND s.Quarter = Scores.Quarter
                 ORDER BY s.Score ASC LIMIT {DROPGAMES})
           GROUP BY Scores.Quarter,PlayerId
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

        rows = []
        with db.getCur() as cur:
            displaycols = ['Name', 'Place'] + columns
            cur.execute("SELECT {columns} FROM Leaderboards"
                    " JOIN Players ON PlayerId = Players.Id"
                    " WHERE Period = ? ORDER BY Date DESC, Place ASC".format(
                        columns=",".join(displaycols)
                    ),
                    (period,)
                )
            rows = [dict(zip(displaycols, row)) for row in cur.fetchall()]

        leaderboards = {}
        for row in rows:
            date = row['Date']
            if date not in leaderboards:
                leaderboards[date] = []

            leaderboards[date] += [row]

        leaderboards = sorted(leaderboards.items(), reverse=True)
        leaderboards = [{'Date': date, 'Scores': scores} for date, scores in leaderboards]

        self.write(json.dumps({'leaderboards':list(leaderboards)}))

def genLeaderboard():
    with db.getCur() as cur:
        leadercols = ['Place'] + columns
        leaderrows = []
        for period, queries in periods.items():
            rows = []
            for query in queries:
                cur.execute(query, (scores.getUnusedPointsPlayerID(),))
                rows += [dict(zip(columns, row)) for row in cur.fetchall()]

            rows.sort(key=lambda row: row['AvgScore'], reverse=True) # sort by score
            places = {}
            for row in rows:
                if row['Date'] not in places:
                    places[row['Date']] = 1
                row['Place'] = places[row['Date']]
                places[row['Date']] += 1

                leaderrow = [row[col] for col in leadercols]
                leaderrows += [leaderrow]

        cur.execute("DELETE FROM Leaderboards")
        query = "INSERT INTO Leaderboards({columns}) VALUES({colvals})".format(
                columns=",".join(leadercols),
                colvals=",".join(["?"] * len(leadercols))
            )
        cur.executemany(query, leaderrows)
