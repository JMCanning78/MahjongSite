#!/usr/bin/env python3

import json
from flask import render_template, Response

import db

from MahjongSite import app

@app.route('/leaderboard/<period>')
@app.route('/leaderboard')
def Leaderboard(period = 'quarter'):
    return render_template("leaderboard.html")

@app.route("/leaderdata/<period>")
@app.route("/leaderdata")
def LeaderData(period = "quarter"):
    with db.getCur() as cur:
        leaderboards = {}
        queries = {
                "annual":[
                    """SELECT strftime('%Y', Scores.Date), Players.Name, ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) / 100 AS AvgScore, COUNT(Scores.Score) AS GameCount, 0
                        FROM Players LEFT JOIN Scores ON Players.Id = Scores.PlayerId
                        GROUP BY strftime('%Y', Date),Players.Id
                        HAVING GameCount >= 4 ORDER BY AvgScore DESC;"""
                ],
                "biannual":[
                    """SELECT strftime('%Y', Scores.Date) || ' ' || case ((strftime('%m', Date) - 1) / 6) when 0 then '1st' when 1 then '2nd' end,
                            Players.Name, ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) / 100 AS AvgScore, COUNT(Scores.Score) AS GameCount, 0
                        FROM Players LEFT JOIN Scores ON Players.Id = Scores.PlayerId
                        GROUP BY strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 6),Players.Id
                        HAVING GameCount >= 4 ORDER BY AvgScore DESC;"""
                ],
                "quarter":[
                    """SELECT strftime('%Y', Scores.Date) || ' ' || case ((strftime('%m', Date) - 1) / 3) when 0 then '1st' when 1 then '2nd' when 2 then '3rd' when 3 then '4th' end,
                            Players.Name, ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) / 100 AS AvgScore, COUNT(Scores.Score) AS GameCount, 0
                        FROM Players LEFT JOIN Scores ON Players.Id = Scores.PlayerId
                        GROUP BY strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 3),Players.Id
                        HAVING GameCount <= 7 ORDER BY AvgScore DESC;""",
                    """SELECT strftime('%Y', Scores.Date) || ' ' || case ((strftime('%m', Date) - 1) / 3) when 0 then '1st' when 1 then '2nd' when 2 then '3rd' when 3 then '4th' end,
                            Players.Name, ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100) / 100 AS AvgScore, COUNT(Scores.Score) + 1 AS GameCount, 1
                        FROM Players LEFT JOIN Scores ON Players.Id = Scores.PlayerId
                        WHERE Scores.Id NOT IN (SELECT Id FROM Scores GROUP BY PlayerId,strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 3) HAVING Score = MIN(Score))
                        GROUP BY strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 3),Players.Id
                        HAVING GameCount > 7 ORDER BY AvgScore DESC;"""
                ]
        }
        if period not in queries:
            period = "quarter"
        rows = []
        for query in queries[period]:
            cur.execute(query)
            rows += cur.fetchall()
        places={}
        rows.sort(key=lambda row: row[2], reverse=True) # sort by score
        for row in rows:
            if row[0] not in leaderboards:
                leaderboards[row[0]] = []
                places[row[0]] = 1
            leaderboard = leaderboards[row[0]]
            leaderboard += [{'place': places[row[0]],
                            'name':row[1],
                            'score':row[2],
                            'count':row[3] if row[4] == 0 else str(row[3] - 1) + " (+1)",
                            'dropped':row[4]}]
            places[row[0]] += 1
        leaders = sorted(list(leaderboards.items()), reverse=True)
        leaderboards = []
        for name, scores in leaders:
            leaderboards += [{'name':name, 'scores':scores}]
        leaderboards={'leaderboards':leaderboards}
        return Response(json.dumps(leaderboards), mimetype = 'application/json')
