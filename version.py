#!/usr/bin/env python3

import handler
from subprocess import *

class VersionHandler(handler.BaseHandler):
    def get(self):
        version = 'Unknown'
        description = ''
        try:
            result = run(['git', 'log', '-n', '1', '--oneline'], stdout=PIPE)
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                if len(parts) > 0:
                    version = parts[0].decode()
                    description = ' '.join([w.decode() for w in parts[1:]])
        except:
            pass
        self.render("version.html", version=version, description=description)
