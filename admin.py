#!/usr/bin/env python3

import json
import handler
import db
import util

class AdminPanelHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self):
        self.render("admin.html")

class ManageUsersHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self):
        with db.getCur() as cur:
            cur.execute("SELECT Users.Id, Email, Password, Admins.Id FROM Users LEFT JOIN Admins ON Admins.Id = Users.Id")
            users = []
            for row in cur.fetchall():
                users += [{
                            "Id":row[0],
                            "Email":row[1],
                            "Admin":row[3] is not None,
                        }]
            self.render("users.html", users = users)

class PromoteUserHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self, q):
        with db.getCur() as cur:
            cur.execute("SELECT Email FROM Users WHERE Id = ?", (q,))
            row = cur.fetchone()
            if len(row) == 0:
                self.render("message.html", message = "User not found", title = "Promote User")
            else:
                self.render("promoteuser.html", email = row[0], q = q)
    @handler.is_admin
    def post(self, q):
        with db.getCur() as cur:
            cur.execute("SELECT EXISTS(SELECT * FROM Users WHERE Id = ?)", (q,))
            if cur.fetchone()[0] == 1:
                cur.execute("INSERT INTO Admins(Id) VALUES(?)", (q,))
            self.redirect("/admin/users")

class DemoteUserHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self, q):
        with db.getCur() as cur:
            cur.execute("SELECT Email FROM Users WHERE Id = ?", (q,))
            row = cur.fetchone()
            if len(row) == 0:
                self.render("message.html", message = "User not found", title = "Demote User")
            else:
                self.render("demoteuser.html", email = row[0], q = q)
    @handler.is_admin
    def post(self, q):
        with db.getCur() as cur:
            cur.execute("SELECT EXISTS(SELECT * FROM Users WHERE Id = ?)", (q,))
            if cur.fetchone()[0] == 1:
                cur.execute("DELETE FROM Admins WHERE Id = ?", (q,))
            self.redirect("/admin/users")

class DeleteGameHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self, q):
        with db.getCur() as cur:
            cur.execute("SELECT Rank, Players.Name, Scores.RawScore / 1000.0, Scores.Score, Scores.Chombos FROM Scores INNER JOIN Players ON Players.Id = Scores.PlayerId WHERE GameId = ?", (q,))
            rows = cur.fetchall()
            if len(rows) == 0:
                self.render("message.html", message = "Game not found", title = "Delete Game")
            else:
                scores = {}
                for row in rows:
                    scores[row[0]] = (row[1], row[2], round(row[3], 2), row[4])
                self.render("deletegame.html", id=q, scores=scores)
    @handler.is_admin
    def post(self, q):
        with db.getCur() as cur:
            cur.execute("SELECT EXISTS(SELECT * FROM Scores WHERE GameId = ?)", (q,))
            if cur.fetchone()[0] == 0:
                self.render("message.html", message = "Game not found", title = "Delete Game")
            else:
                cur.execute("DELETE FROM Scores WHERE GameId = ?", (q,))
                self.redirect("/history")

class EditGameHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self, q):
        with db.getCur() as cur:
            cur.execute("SELECT Rank, Players.Name, Scores.RawScore, Scores.Chombos, Scores.Date FROM Scores INNER JOIN Players ON Players.Id = Scores.PlayerId WHERE GameId = ? ORDER BY Rank", (q,))
            rows = cur.fetchall()
            if len(rows) == 0:
                self.render("message.html", message = "Game not found", title = "Edit Game")
            else:
                self.render("editgame.html", id=q, scores=json.dumps(rows).replace("'", "\\'").replace("\\\"", "\\\\\""))
    @handler.is_admin_ajax
    def post(self, q):
        scores = self.get_argument('scores', None)
        gamedate = self.get_argument('gamedate', None)

        if scores is None:
            self.write('{"status":1, "error":"Please enter some scores"}')
            return

        scores = json.loads(scores)

        if len(scores) != 4 and len(scores) != 5:
            self.write('{"status":1, "error":"Please enter 4 or 5 scores"}')
            return

        total = 0
        for score in scores:
            total += score['score']
        if total != len(scores) * 25000:
            self.write('{"status":1, "error":' + "Scores do not add up to " + len(scores) * 25000 + '}')
            return

        with db.getCur() as cur:
            cur.execute("SELECT GameId FROM Scores WHERE GameId = ?", (q,))
            row = cur.fetchone()
            if len(row) == 0:
                self.write('{"status":1, "error":"Game not found"}')
                return
            gameid = row[0]
            print(gameid)
            print(gamedate)

            for i in range(0, len(scores)):
                score = scores[i]
                if score['player'] == "":
                    self.write('{"status":1, "error":"Please enter all player names"}')
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
        self.write('{"status":0}')
