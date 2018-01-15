#!/usr/bin/env python3

import json

import handler
import db
import util
import settings
import leaderboard
import scores

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
                db.make_backup()
                cur.execute("DELETE FROM Scores WHERE GameId = ?", (q,))
                leaderboard.genLeaderboard()
                self.redirect("/history")

class EditGameHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self, q):
        with db.getCur() as cur:
            cur.execute("SELECT Rank, Players.Name, Scores.RawScore, Scores.Chombos, Scores.Date, Players.Id FROM Scores INNER JOIN Players ON Players.Id = Scores.PlayerId WHERE GameId = ? ORDER BY Rank", (q,))
            rows = cur.fetchall()
            if len(rows) == 0:
                self.render("message.html", message = "Game not found", title = "Edit Game")
            else:
                unusedPoints = None
                # UnusedPointsPlayer always sorted last in rank
                if rows[-1][5] == scores.getUnusedPointsPlayerID():
                    unusedPoints = rows[-1][2]
                self.render("editgame.html", id=q,
                            scores=json.dumps(rows).replace("'", "\\'")
                            .replace("\\\"", "\\\\\""),
                            unusedPoints=unusedPoints,
                            unusedPointsIncrement=scores.unusedPointsIncrement())
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

        db.make_backup()
        self.write(json.dumps(scores.addGame(scores, gamedate, gameid)))

class EditQuarterHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self, q):
        with db.getCur() as cur:
            cur.execute("SELECT Quarter, Gamecount, UnusedPointsIncrement "
                        "FROM Quarters WHERE Quarter = ? ORDER BY Quarter DESC",
                        (q,))
            rows = cur.fetchall()
            if len(rows) == 0:
                rows = [(q, settings.DROPGAMES, scores.unusedPointsIncrement())]
            if len(rows) > 1:
                self.render("message.html",
                            message = "Multiple entries in database for Quarter {0}".format(q),
                            title = "Database Error",
                            next = "Manage Quarters",
                            next_url = "/admin/quarters")
            else:
                self.render("editquarter.html", quarters=rows)

    @handler.is_admin
    def post(self, q):
        quarter = q
        gamecount = self.get_argument('gamecount', None)
        unusedPointsIncrement = self.get_argument('unusedPointsIncrement', None)
        with db.getCur() as cur:
            cur.execute("DELETE FROM Quarters WHERE Quarter = ?;", (quarter,))
            cur.execute("INSERT INTO Quarters(Quarter, Gamecount, "
                        "UnusedPointsIncrement) VALUES (?,?,?);",
                        (quarter, gamecount, unusedPointsIncrement))

        leaderboard.genLeaderboard()

        self.render("message.html",
                    message = "Quarter {0} updated".format(quarter),
                    title = "Quarter Updated",
                    next = "Update more quarters",
                    next_url = "/admin/quarters")

class QuartersHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self):
        with db.getCur() as cur:
            cur.execute(
                "SELECT DISTINCT Scores.Quarter, Gamecount, "
                " COALESCE(UnusedPointsIncrement, ?)"
                " FROM Scores LEFT OUTER JOIN Quarters"
                " ON Scores.Quarter = Quarters.Quarter"
                " ORDER BY Scores.Quarter DESC",
                (scores.unusedPointsIncrement(),))
            rows = cur.fetchall()

            self.render("quarters.html",
                        message = "No quarters found" if len(rows) == 0 else "",
                        quarters=rows)

class DeleteQuarterHandler(handler.BaseHandler):
    @handler.is_admin
    def get(self, q):
        with db.getCur() as cur:
            cur.execute("SELECT Quarter, Gamecount FROM Quarters "
                        "WHERE Quarter = ? ORDER BY Quarter DESC", (q,))
            rows = cur.fetchall()
            if len(rows) == 0:
                self.render("message.html",
                            message = "Quarter {0} not found".format(q),
                            title = "Quarter Not Found",
                            next = "Manage quarters",
                            next_url = "/admin/quarters")
            elif len(rows) == 1:
                cur.execute("DELETE FROM Quarters WHERE Quarter = ?", (q,))
                self.render("message.html",
                            message = "Quarter {0} deleted".format(q),
                            title = "Quarter Deleted",
                            next = "Manage quarters",
                            next_url = "/admin/quarters")
                leaderboard.genLeaderboard()
            else:
                self.render("quarters.html",
                            message = ("Error: Multiple quarters named {0} "
                                       "found. See Adminstrator.").format(q),
                            quarters=rows)

