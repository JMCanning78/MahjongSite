#!/usr/bin/env python3

import handler
import os.path
from pygit2 import Repository

class VersionHandler(handler.BaseHandler):
    def get(self):
        version = 'Unknown'
        description = ''
        author = ''
        committer = ''
        try:
            commit = Repository(os.path.dirname(__file__)).head.get_object()
            version = commit.id
            description = commit.message
            author = commit.author.name
            committer = commit.committer.name
        except:
            pass
        self.render(
            "version.html",
            version=version,
            description=description,
            author=author,
            committer=committer
        )
