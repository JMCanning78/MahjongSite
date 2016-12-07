#!/usr/bin/env python3

import json
import db
import util

from functools import wraps
from flask import request, session, render_template, redirect, g, url_for, Response

from MahjongSite import app

def is_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'user' in session:
            return redirect(url_for('Login', next=request.path[1:]))
        if not 'admin' in session or not session['admin']:
            return render_template("message.html", message = "You must be admin to do that")
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@is_admin
def AdminPanel():
    return render_template("admin.html")

@app.route('/admin/users', methods=["GET", "POST"])
@is_admin
def ManageUsers():
    if request.method == "GET":
        with db.getCur() as cur:
            cur.execute("SELECT Users.Id, Email, Password, Admins.Id FROM Users LEFT JOIN Admins ON Admins.Id = Users.Id")
            users = []
            for row in cur.fetchall():
                users += [{
                            "Id":row[0],
                            "Email":row[1],
                            "Admin":row[3] is not None,
                        }]
            return render_template("users.html", users = users)

@app.route('/admin/promote/<int:user>', methods=["GET", "POST"])
@is_admin
def PromoteUser(user):
    if request.method == "GET":
        with db.getCur() as cur:
            cur.execute("SELECT Email FROM Users WHERE Id = ?", (user,))
            row = cur.fetchone()
            if len(row) == 0:
                return render_template("message.html", message = "User not found", title = "Promote User")
            else:
                cur.execute("SELECT EXISTS(SELECT * FROM Admins WHERE Id = ?)", (user,))
                if cur.fetchone()[0] == 1:
                    return render_template("message.html", message = "User already admin", title = "Promote User")
                else:
                    return render_template("promoteuser.html", email = row[0], user = user)
    elif request.method == "POST":
        with db.getCur() as cur:
            cur.execute("SELECT EXISTS(SELECT * FROM Users WHERE Id = ?)", (user,))
            if cur.fetchone()[0] == 1:
                cur.execute("INSERT INTO Admins(Id) VALUES(?)", (user,))
            return redirect("/admin/users")

@app.route('/admin/demote/<int:user>', methods=["GET", "POST"])
@is_admin
def DemoteUser(user):
    if request.method == "GET":
        with db.getCur() as cur:
            cur.execute("SELECT Email FROM Users WHERE Id = ?", (user,))
            row = cur.fetchone()
            if len(row) == 0:
                return render_template("message.html", message = "User not found", title = "Demote User")
            else:
                cur.execute("SELECT EXISTS(SELECT * FROM Admins WHERE Id = ?)", (user,))
                if cur.fetchone()[0] == 0:
                    return render_template("message.html", message = "User already non-admin", title = "Demote User")
                else:
                    return render_template("demoteuser.html", email = row[0], user = user)
    elif request.method == "POST":
        with db.getCur() as cur:
            cur.execute("SELECT EXISTS(SELECT * FROM Users WHERE Id = ?)", (user,))
            if cur.fetchone()[0] == 1:
                cur.execute("DELETE FROM Admins WHERE Id = ?", (user,))
            return redirect("/admin/users")

@app.route('/admin/delete/<int:q>', methods=["GET", "POST"])
@is_admin
def DeleteGame(q):
    if request.method == "GET":
        with db.getCur() as cur:
            cur.execute("SELECT Rank, Players.Name, Scores.RawScore / 1000.0, Scores.Score, Scores.Chombos FROM Scores INNER JOIN Players ON Players.Id = Scores.PlayerId WHERE GameId = ?", (q,))
            rows = cur.fetchall()
            if len(rows) == 0:
                return render_template("message.html", message = "Game not found", title = "Delete Game")
            else:
                scores = {}
                for row in rows:
                    scores[row[0]] = (row[1], row[2], round(row[3], 2), row[4])
                return render_template("deletegame.html", id=q, scores=scores)
    elif request.method == "POST":
        with db.getCur() as cur:
            cur.execute("SELECT EXISTS(SELECT * FROM Scores WHERE GameId = ?)", (q,))
            if cur.fetchone()[0] == 0:
                return render_template("message.html", message = "Game not found", title = "Delete Game")
            else:
                cur.execute("DELETE FROM Scores WHERE GameId = ?", (q,))
                return redirect("/history")

@app.route('/admin/edit/<int:q>', methods=["GET", "POST"])
@is_admin
def EditGame(q):
    if request.method == "GET":
        with db.getCur() as cur:
            cur.execute("SELECT Rank, Players.Name, Scores.RawScore, Scores.Chombos, Scores.Date FROM Scores INNER JOIN Players ON Players.Id = Scores.PlayerId WHERE GameId = ? ORDER BY Rank", (q,))
            rows = cur.fetchall()
            if len(rows) == 0:
                return render_template("message.html", message = "Game not found", title = "Edit Game")
            else:
                return render_template("editgame.html", id=q, scores=json.dumps(rows).replace("'", "\\'").replace("\\\"", "\\\\\""))
    elif request.method == "POST":
        scores = request.form['scores']
        gamedate = request.form['gamedate']

        if scores is None:
            return Response('{"status":1, "error":"Please enter some scores"}', mimetype = 'application/json')
            return

        scores = json.loads(scores)

        if len(scores) != 4 and len(scores) != 5:
            return Response('{"status":1, "error":"Please enter 4 or 5 scores"}', mimetype = 'application/json')
            return

        total = 0
        for score in scores:
            total += score['score']
        if total != len(scores) * 25000:
            return Response('{"status":1, "error":' + "Scores do not add up to " + len(scores) * 25000 + '}', mimetype = 'application/json')
            return

        with db.getCur() as cur:
            cur.execute("SELECT GameId FROM Scores WHERE GameId = ?", (q,))
            row = cur.fetchone()
            if len(row) == 0:
                return Response('{"status":1, "error":"Game not found"}', mimetype = 'application/json')
                return
            gameid = row[0]
            print(gameid)
            print(gamedate)

            for i in range(0, len(scores)):
                score = scores[i]
                if score['player'] == "":
                    return Response('{"status":1, "error":"Please enter all player names"}', mimetype = 'application/json')
                    return
            cur.execute("DELETE FROM Scores WHERE GameId = ?", (gameid,))
            for i in range(0, len(scores)):
                score = scores[i]
                cur.execute("SELECT Id FROM Players WHERE Id = ? OR Name = ?", (score['player'], score['player']))
                player = cur.fetchone()
                if player is None or len(player) == 0:
                    cur.execute("INSERT INTO Players(Name) VALUES(?)", (score['player'],))
                    cur.execute("SELECT Id FROM Players WHERE Name = ?", (score['player'],))
                    player = cur.fetchone()
                player = player[0]

                adjscore = util.getScore(score['newscore'], len(scores), i + 1)
                cur.execute("INSERT INTO Scores(GameId, PlayerId, Rank, PlayerCount, RawScore, Chombos, Score, Date) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (gameid, player, i + 1, len(scores), score['score'], score['chombos'], adjscore, gamedate))
        return Response('{"status":0}', mimetype = 'application/json')
