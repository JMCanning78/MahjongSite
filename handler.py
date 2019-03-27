#!/usr/bin/env python3
import tornado.web

import db
import settings
from util import stringify

class BaseHandler(tornado.web.RequestHandler):
    def get_current_player(self):
        return stringify(self.get_secure_cookie("playerId"))
    def get_current_player_name(self):
        return stringify(self.get_secure_cookie("playerName"))
    def get_current_user(self):
        if settings.DEVELOPERMODE:
            return "1"
        else:
            return stringify(self.get_secure_cookie("user"))

    def get_current_user_name(self):
        if (getattr(self, 'current_user_name', None) and
            self.current_user == self.current_user_ID):
            return self.current_user_name
        self.current_user_ID = self.current_user
        if self.current_user:
            with db.getCur() as cur:
                cur.execute("SELECT Email FROM Users WHERE Id = ?",
                            (self.current_user,))
                email = cur.fetchone()
                if isinstance(email, tuple):
                    # Find unique prefix for account name
                    try:
                        acctname, domain = email[0].split('@', 1)
                    except ValueError as e:
                        acctname = email[0]
                    cur.execute(
                        "SELECT Email FROM Users WHERE Email like ?",
                        (acctname + '%' if acctname != email[0] else acctname,))
                    emails = [x[0] for x in cur.fetchall()]
                    for n in range(len(acctname), len(email[0])):
                        if sum([1 if e.startswith(email[0][0:n]) else 0
                                for e in emails]) <= 1:
                            acctname = email[0][0:n]
                            break
                    self.current_user_name = acctname
                    return self.current_user_name
        return None

    def get_is_admin(self):
        if settings.DEVELOPERMODE:
            return True
        else:
            return stringify(self.get_secure_cookie("admin")) == "1"

    def get_stylesheet(self):
        return stringify(self.get_secure_cookie("stylesheet"))

    def render(self, template_name, **kwargs):
        tornado.web.RequestHandler.render(
            self,
            template_name,
            stylesheet = self.get_stylesheet(),
            current_user = self.current_user,
            current_user_name = self.get_current_user_name(),
            is_admin = self.get_is_admin(),
            SponsorLink = settings.SPONSORLINK,
            **kwargs
        )

def is_admin(func):
    def func_wrapper(self, *args, **kwargs):
        if not self.get_is_admin():
            self.render("message.html", message = "You must be admin to do that")
        else:
            func(self, *args, **kwargs)

    return func_wrapper

def is_admin_ajax(func):
    def func_wrapper(self, *args, **kwargs):
        if not self.get_is_admin():
            self.write('{"status":1, "error":"You must be admin to do that"}')
        else:
            func(self, *args, **kwargs)

    return func_wrapper
