#!/usr/bin/env python3

import json

import handler
import db

class TimersHandler(handler.BaseHandler):
    def get(self):
        self.render("timers.html")

class GetTimersHandler(handler.BaseHandler):
    def get(self):
        with db.getCur() as cur:
            cur.execute("SELECT Id, Name, Time, Duration FROM Timers")
            self.write(json.dumps({"timers":[{"id":row[0], "name":row[1],"time":row[2],"duration":row[3]} for row in cur.fetchall()]}))

class AddTimer(handler.BaseHandler):
    #@torando.web.authenticated
    def post(self):
        ret = {"status":"error","message":"Unknown error occurred"}
        name = self.get_argument("name", None)
        duration = self.get_argument("duration", None)
        with db.getCur() as cur:
            cur.execute("INSERT INTO Timers(Name, Duration) VALUES(?,?)", (name,duration))
            ret["status"] = 0
            ret["message"] = "Success"
        self.write(ret)

class StartTimer(handler.BaseHandler):
    #@torando.web.authenticated
    def post(self):
        ret = {"status":"error","message":"Unknown error occurred"}
        id = self.get_argument("id", None)
        with db.getCur() as cur:
            if id == "all":
                cur.execute("UPDATE Timers SET Time = datetime('now','localtime', '+' || Duration || ' minutes')")
            elif id is not None:
                cur.execute("UPDATE Timers SET Time = datetime('now','localtime', '+' || Duration || ' minutes') WHERE Id = ?", (id,))
            else:
                cur.execute("UPDATE Timers SET Time = datetime('now','localtime', '+' || Duration || ' minutes') WHERE Time IS NULL OR Time < datetime('now', 'localtime');")
            ret["status"] = 0
            ret["message"] = "Success"
        self.write(ret)

class ClearTimers(handler.BaseHandler):
    #@torando.web.authenticated
    def post(self):
        ret = {"status":"error","message":"Unknown error occurred"}
        with db.getCur() as cur:
            cur.execute("DELETE FROM Timers")
            ret["status"] = 0
            ret["message"] = "Success"
        self.write(ret)
