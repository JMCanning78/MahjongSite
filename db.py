#!/usr/bin/env python3

__doc__ = """
Manage database for mahjong players, scores, users, etc.
"""

import warnings
import sqlite3
import datetime
import re
import collections
import shutil
import os
import logging
import argparse

import util
import settings
from sqlite_schema import *

log = logging.getLogger("WebServer")

class getCur():
    con = None
    cur = None
    def __enter__(self):
        self.con = sqlite3.connect(settings.DBFILE)
        self.cur = self.con.cursor()
        self.cur.execute("PRAGMA foreign_keys = 1;")
        return self.cur
    def __exit__(self, type, value, traceback):
        if self.cur and self.con and not value:
            self.cur.close()
            self.con.commit()
            self.con.close()

        return False

schema = collections.OrderedDict({
    'Players': [
        'Id INTEGER PRIMARY KEY AUTOINCREMENT',
        'Name TEXT UNIQUE ON CONFLICT ABORT',
        'MeetupName TEXT UNIQUE ON CONFLICT ABORT',
        'Symbol TEXT'
    ],
    'Scores': [
        'Id INTEGER PRIMARY KEY AUTOINCREMENT',
        'GameId INTEGER',
        'PlayerId INTEGER',
        'Rank TINYINT',
        'PlayerCount TINYINT',
        'RawScore INTEGER',
        'Score REAL',
        'Date DATE',
        'Chombos INTEGER',
        'Quarter TEXT',
        'DeltaRating REAL',
        'FOREIGN KEY(PlayerId) REFERENCES Players(Id) ON DELETE CASCADE'
    ],
    'CurrentPlayers': [
        'PlayerId INTEGER PRIMARY KEY',
        'Priority TINYINT',
        'FOREIGN KEY(PlayerId) REFERENCES Players(Id) ON DELETE CASCADE'
    ],
    'CurrentTables': [
        'Id INTEGER PRIMARY KEY AUTOINCREMENT',
        'PlayerId INTEGER',
        'FOREIGN KEY(PlayerId) REFERENCES Players(Id) ON DELETE CASCADE'
    ],
    'Users': [
        'Id INTEGER PRIMARY KEY AUTOINCREMENT',
        'Email TEXT NOT NULL',
        'Password TEXT NOT NULL',
        'PlayerId INTEGER',
        'FOREIGN KEY(PlayerId) REFERENCES Players(Id) ON DELETE SET NULL',
        'UNIQUE(Email)'
    ],
    'Admins': [
        'Id INTEGER PRIMARY KEY NOT NULL',
        'FOREIGN KEY(Id) REFERENCES Users(Id) ON DELETE CASCADE'
    ],
    'ResetLinks': [
        'Id CHAR(32) PRIMARY KEY NOT NULL',
        'User INTEGER',
        'Expires DATETIME',
        'FOREIGN KEY(User) REFERENCES Users(Id)'
    ],
    'VerifyLinks': [
        'Id CHAR(32) PRIMARY KEY NOT NULL',
        'Email TEXT NOT NULL',
        'Expires DATETIME'
    ],
    'Quarters': [
        'Quarter TEXT PRIMARY KEY NOT NULL',
        'ScorePerPlayer INTEGER DEFAULT 25000',
        'UnusedPointsIncrement INTEGER DEFAULT 0',
        'GameCount INTEGER NOT NULL',
        'QualifyingGames INTEGER NOT NULL DEFAULT 1',
        'QualifyingDistinctDates INTEGER NOT NULL DEFAULT 1'
    ],
    'Settings': [
        'UserId INTEGER',
        'Setting TEXT NOT NULL',
        'Value SETTING NOT NULL',
        'FOREIGN KEY(UserId) REFERENCES Users(Id)'
    ],
    'Timers': [
        'Id INTEGER PRIMARY KEY',
        'Name TEXT',
        'Duration INTEGER',
        'Time DATETIME'
    ],
    'Leaderboards': [
        'Period TEXT',
        'Date TEXT',
        'PlayerId INTEGER',
        'Place INTEGER',
        'AvgScore REAL',
        'GameCount INTEGER',
        'DropGames INTEGER',
        'DateCount INTEGER',
        'FOREIGN KEY(PlayerId) REFERENCES Players(Id) ON DELETE CASCADE'
    ],
    'Memberships': [
        'PlayerId INTEGER',
        'QuarterId TEXT',
        'FOREIGN KEY(PlayerId) REFERENCES Players(Id) ON DELETE CASCADE',
        'FOREIGN KEY(QuarterId) REFERENCES Quarters(Quarter) ON DELETE CASCADE',
        'UNIQUE(PlayerId, QuarterId)'
    ],
})

def init(force=False, dbfile=settings.DBFILE, verbose=0):
    existing_schema = get_sqlite_db_schema(dbfile)
    desired_schema = parse_database_schema(schema)

    if not compare_and_prompt_to_upgrade_database(
            desired_schema, existing_schema, dbfile,
            ordermatters=False, prompt_prefix='SCHEMA CHANGE: ',
            force_response='y' if force else None,
            backup_dir=settings.DBBACKUPS,
            backup_prefix=settings.DBDATEFORMAT + '-', verbose=verbose):
        log.error('Database upgrade during initialization {}.'.format(
            'failed' if force else 'was either cancelled or failed'))

def make_backup():
    backupdb = datetime.datetime.now().strftime(settings.DBDATEFORMAT) + "-" + os.path.split(settings.DBFILE)[1]
    backupdb = os.path.join(settings.DBBACKUPS, backupdb)
    log.info("Making backup of database {0} to {1}".format(
        settings.DBFILE, backupdb))

    if not os.path.isdir(settings.DBBACKUPS):
        os.mkdir(settings.DBBACKUPS)
    shutil.copyfile(settings.DBFILE, backupdb)

def words(spec):
    return re.findall(r'\w+', spec)

def table_field_names(tablename):
    return [words(fs)[0] for fs in schema.get(tablename, [])
            if not words(fs)[0].upper() in [
                    'FOREIGN', 'UNIQUE', 'CONSTRAINT', 'PRIMARY', 'CHECK']]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'database', default=settings.DBFILE, nargs='?',
        help='SQLite3 database file to check.')
    parser.add_argument(
        '-f', '--force', default=False, action='store_true',
        help='Force an upgrade rather than prompting')
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Add verbose comments.')

    args = parser.parse_args()

    init(force=args.force, dbfile=args.database, verbose=args.verbose)
