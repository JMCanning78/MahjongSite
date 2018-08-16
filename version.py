#!/usr/bin/env python3

import handler
import os.path
try:
    from pygit2 import Repository
except:
    import collections
    authorRecord = collections.namedtuple('Author', 'name, email')
    committerRecord = collections.namedtuple('Committer', 'name, email')
    nodeRecord = collections.namedtuple('Node', 
                                        'id, message, author, committer')
    class Node(object):
        def get_object(self):
            return nodeRecord("unknown commit",
                              "Missing pygit2 to determine commit",
                              authorRecord("unknown", ""),
                              committerRecord("unknown", ""))
    class Repository(object):
        def __init__(self, filename=None):
            self.head = Node()

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
