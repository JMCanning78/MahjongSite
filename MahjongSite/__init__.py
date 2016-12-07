import os
from flask import Flask

from quemail import QueMail
import settings
import util
import db

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or util.randString(32)
db.init()
if hasattr(settings, 'EMAILSERVER'):
    qm = QueMail.get_instance()
    if not hasattr(qm, '_queue'):
        qm.init(settings.EMAILSERVER, settings.EMAILUSER, settings.EMAILPASSWORD, settings.EMAILPORT, True)
        qm.start()

import MahjongSite.main
import MahjongSite.leaderboard
import MahjongSite.history
import MahjongSite.login
import MahjongSite.admin
import MahjongSite.seating
