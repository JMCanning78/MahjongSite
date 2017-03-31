#!/usr/bin/env python3
import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

    def get_is_admin(self):
        return self.get_secure_cookie("admin") == "1"

    def get_stylesheet(self):
        return self.get_secure_cookie("stylesheet")

    def render(self, template_name, **kwargs):
            tornado.web.RequestHandler.render(self,
                    template_name,
                    stylesheet = self.get_stylesheet(),
                    current_user = self.current_user,
                    is_admin = self.get_is_admin(),
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
