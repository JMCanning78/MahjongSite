#!/usr/bin/env python3
import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

    def render(self, template_name, **kwargs):
            tornado.web.RequestHandler.render(self,
                    template_name,
                    current_user = self.current_user,
                    **kwargs
            )
