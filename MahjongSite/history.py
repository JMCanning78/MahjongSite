#!/usr/bin/env python3

import math
from flask import render_template

import db

from MahjongSite import app

@app.route('/history/<int:page>')
@app.route('/history')
def History(page = 1):
    page -= 1
    PERPAGE = 5
    with db.getCur() as cur:
        cur.execute("SELECT DISTINCT Date FROM Scores ORDER BY Date DESC")
        dates = cur.fetchall()
        gamecount = len(dates)
        if gamecount > 0:
            cur.execute("SELECT Scores.GameId, strftime('%Y-%m-%d', Scores.Date), Rank, Players.Name, Scores.RawScore / 1000.0, Scores.Score, Scores.Chombos FROM Scores INNER JOIN Players ON Players.Id = Scores.PlayerId WHERE Scores.Date BETWEEN ? AND ? GROUP BY Scores.Id ORDER BY Scores.Date ASC;", (dates[min(page * PERPAGE + PERPAGE - 1, gamecount - 1)][0], dates[min(page * PERPAGE, gamecount - 1)][0]))
            rows = cur.fetchall()
            games = {}
            for row in rows:
                if row[0] not in games:
                    games[row[0]] = {'date':row[1], 'scores':{}, 'id':row[0]}
                games[row[0]]['scores'][row[2]] = (row[3], row[4], round(row[5], 2), row[6])
            maxpage = math.ceil(gamecount * 1.0 / PERPAGE)
            pages = range(max(1, page + 1 - 10), int(min(maxpage, page + 1 + 10) + 1))
            games = sorted(games.values(), key=lambda x: x["date"], reverse=True)
            if page != 0:
                prev = page
            else:
                prev = None
            if page + 1 < maxpage:
                nex = page + 2
            else:
                nex = None
            return render_template("history.html", error=None, games=games, curpage=page + 1, pages=pages, gamecount=gamecount, nex = nex, prev = prev)
        else:
            return render_template("message.html", message="No games entered thusfar", title="Game History")

@app.route('/playerhistory/<player>/<int:page>')
@app.route('/playerhistory/<player>')
def PlayerHistory(player, page = 1):
    page -= 1
    PERPAGE = 10
    with db.getCur() as cur:
        cur.execute("SELECT Id,Name FROM Players WHERE Id = ? OR Name = ?", (player, player))
        player = cur.fetchone()
        if len(player) == 0:
            return render_template("message.html", message="Couldn't find that player", title="User Game History")
            return
        name = player[1]
        player = player[0]
        cur.execute("SELECT DISTINCT GameId FROM Scores WHERE PlayerId = ? ORDER BY Date DESC", (player,))
        games = [i[0] for i in cur.fetchall()]
        gamecount = len(games)
        print min(page * PERPAGE + PERPAGE - 1, gamecount - 1)
        if gamecount > 0:
            thesegames = games[min(page * PERPAGE, gamecount - 1):min(page * PERPAGE + PERPAGE - 1, gamecount - 1)]
            placeholder= '?' # For SQLite. See DBAPI paramstyle
            placeholders= ', '.join(placeholder for i in range(len(thesegames)))
            print(placeholders)
            cur.execute("SELECT Scores.GameId, strftime('%Y-%m-%d', Scores.Date), Rank, Players.Name, Scores.RawScore / 1000.0, Scores.Score, Scores.Chombos FROM Scores INNER JOIN Players ON Players.Id = Scores.PlayerId WHERE Scores.GameId IN (" + placeholders + ") GROUP BY Scores.Id ORDER BY Scores.Date ASC;", thesegames)
            rows = cur.fetchall()
            games = {}
            for row in rows:
                if row[0] not in games:
                    games[row[0]] = {'date':row[1], 'scores':{}, 'id':row[0]}
                games[row[0]]['scores'][row[2]] = (row[3], row[4], round(row[5], 2), row[6])
            maxpage = math.ceil(gamecount * 1.0 / PERPAGE)
            pages = range(max(1, page + 1 - 10), int(min(maxpage, page + 1 + 10) + 1))
            games = sorted(games.values(), key=lambda x: x["date"], reverse=True)
            if page != 0:
                prev = page
            else:
                prev = None
            if page + 1 < maxpage:
                nex = page + 2
            else:
                nex = None
            return render_template("userhistory.html",
                    error=None,
                    games=games,
                    curpage=page + 1,
                    pages=pages,
                    gamecount=gamecount,
                    nex = nex,
                    prev = prev,
                    user = name,
                    player = player)
        else:
            return render_template("message.html", message="No games entered thusfar", title="Game History", user = name)

@app.route('/playerstats/<player>')
def PlayerStats(player):
    with db.getCur() as cur:
        cur.execute("SELECT Id,Name FROM Players WHERE Id = ? OR Name = ?", (player, player))
        player = cur.fetchone()
        if len(player) == 0:
            return render_template("stats.html", error="Couldn't find that player")
            return
        name = player[1]
        player = player[0]
        cur.execute("SELECT Max(Score),MIN(Score),COUNT(*),ROUND(SUM(Score) * 1.0/COUNT(*) * 100) / 100,ROUND(SUM(Rank) * 1.0/COUNT(*) * 100) / 100 FROM Scores WHERE PlayerId = ?", (player,))
        row = cur.fetchone()
        maxscore = row[0]
        minscore = row[1]
        numgames = row[2]
        avgscore = row[3]
        avgrank = row[4]
        cur.execute("SELECT ROUND(Sum(Score) * 1.0 / COUNT(*) * 100) / 100, ROUND(Sum(Rank) * 1.0 / COUNT(*) * 100) / 100 FROM (SELECT * FROM Scores WHERE PlayerId = ? ORDER BY Date DESC LIMIT 5)", (player,))
        row = cur.fetchone()
        avgscore5 = row[0]
        avgrank5 = row[1]
        return render_template("stats.html",
                error = None,
                name = name,
                maxscore = maxscore,
                minscore = minscore,
                numgames = numgames,
                avgscore = avgscore,
                avgrank  = avgrank,
                avgscore5 = avgscore5,
                avgrank5 = avgrank5
            )

