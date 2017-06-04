#!/usr/bin/env python3

import json

import handler
import db
import util
import settings

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

        scores = json.loads(scores)

        with db.getCur() as cur:
            cur.execute("SELECT GameId FROM Scores WHERE GameId = ?", (q,))
            row = cur.fetchone()
            if len(row) == 0:
                self.write('{"status":1, "error":"Game not found"}')
                return
            gameid = row[0]

        self.write(json.dumps(db.addGame(scores, gamedate, gameid)))

class AddQuarterHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self):
        with db.getCur() as cur:
            cur.execute("SELECT DISTINCT Quarter FROM Scores")
            rows = cur.fetchall()
            rows = [row[0] for row in rows]
            if len(rows) == 0:
                self.render("message.html", message = "No scores in database", title = "Add Quarter Gamecount")
            else:
                self.render("addquarter.html", quarters=rows, dropgames=settings.DROPGAMES)
    @handler.is_admin
    def post(self):
        quarter = self.get_argument('quarter', None)
        gamecount = self.get_argument('gamecount', None)
        with db.getCur() as cur:
            cur.execute("DELETE FROM Quarters WHERE Quarter = ?;", (quarter,))
            cur.execute("INSERT INTO Quarters(Quarter, Gamecount) VALUES (?,?);", (quarter, gamecount))

        self.render("message.html", message = "Quarter updated", title = "Add Quarter Gamecount")

class QuartersHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self):
        with db.getCur() as cur:
            cur.execute("SELECT Quarter, Gamecount FROM Quarters")
            rows = cur.fetchall()
            if len(rows) == 0:
                self.render("quarters.html", message = "No quarters found")
            else:
                self.render("quarters.html", quarters=rows)

class DeleteQuarterHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self, q):
        with db.getCur() as cur:
            cur.execute("SELECT Quarter FROM Quarters WHERE Quarter = ?", (q,))
            row = cur.fetchone()
            if row == None:
                self.render("message.html", message = "Quarter not found", title = "Delete Quarter Gamecounts")
            else:
                self.render("quarters.html", quarter=row[0])
    @handler.is_admin
    def get(self, q):
        with db.getCur() as cur:
            cur.execute("SELECT Quarter FROM Quarters WHERE Quarter = ?", (q,))
            row = cur.fetchone()
            if row == None:
                self.render("message.html", message = "Quarter not found", title = "Delete Quarter Gamecounts")
            else:
                cur.execute("DELETE FROM Quarters WHERE Quarter = ?", (row[0],))
                self.render("message.html", message = "Quarter deleted", title = "Delete Quarter Gamecount")

