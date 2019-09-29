#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib
import urllib.request
import json
import tornado.web
import random
import datetime
import math
from operator import itemgetter
import logging
import traceback

import db
import handler
import settings
import scores

log = logging.getLogger("WebServer")

def meetup_ready():
    return (settings.MEETUP_CONSUMER_KEY and settings.MEETUP_GROUPNAME and
            len(settings.MEETUP_CONSUMER_KEY) > 1 and
            len(settings.MEETUP_GROUPNAME) > 1)

def target_meetup_date():
    debug = settings.DEVELOPERMODE;  # Set True to force a particular date when testing meetup
    return datetime.date(2018, 9, 3) if debug else datetime.date.today()

def make_meetup_request(endpoint, accessToken, data):
    url = "https://api.meetup.com"
    if endpoint.startswith("/"):
        url += endpoint
    else:
        url += "/" + endpoint
    headers = {
        'User-Agent': settings.USER_AGENT,
        'Authorization': "Bearer {}".format(accessToken)
    }

    data = urllib.parse.urlencode(data)
    req = urllib.request.Request(
            url + "?" + data,
            headers=headers
          )
    with urllib.request.urlopen(req) as response:
        responseText = response.read()
        return json.loads(
                   responseText
                   .decode('utf-8')
               )
    return None


class MeetupEventHandler(handler.BaseHandler):
    def current_meetup_event(self):
        eventlist = []
        event_params = {
            'page':20
        }
        if target_meetup_date() < datetime.date.today():
            event_params['status'] = 'past'
            event_params['desc'] = True

        access_token = self.get_secure_cookie("access_token", None)
        if access_token is not None:
            access_token = access_token.decode('ascii')

        # TODO: Refresh token if request fails due to expired access key
        #refresh_token = self.get_secure_cookie("refresh_token").decode('ascii')

        events = make_meetup_request(
            "/{}/events".format(settings.MEETUP_GROUPNAME),
            access_token,
            event_params
        )

        for result in events:
            if datetime.date.fromtimestamp(
                    result['time'] / 1000) == target_meetup_date():
                return result

        if len(events) > 0:
            return events[0]
        else:
            return None

class SeatingHandler(MeetupEventHandler):
    def get(self):
        event = None
        if meetup_ready():
            try:
                event = self.current_meetup_event()
            except Exception as e:
                pass
        if event is None:
            meetupDate = target_meetup_date()
        else:
            meetupDate = datetime.date.fromtimestamp(event['time'] / 1000)

        self.render("seating.html", meetup_ok = meetup_ready(),
                    today=meetupDate.strftime('%a %d-%b'))

class RegenTables(handler.BaseHandler):
    @tornado.web.authenticated
    def post(self):
        self.set_header('Content-Type', 'application/json')
        with db.getCur() as cur:
            cur.execute("SELECT PlayerId, Priority FROM CurrentPlayers"
                        " WHERE Priority < 2")
            priorities = dict(cur.fetchall())
            players = list(priorities.keys())
            playergames = playerGames(players, cur)
            tables = bestArrangement(players, playergames, priorities)
            cur.execute("DELETE FROM CurrentTables")
            if len(players) > 0:
                cur.execute("INSERT INTO CurrentTables(PlayerId) VALUES" + ",".join(["(?)"] * len(players)), tables)
            self.write('{"status":0}')

class CurrentPlayers(handler.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        with db.getCur() as cur:
            self.set_header('Content-Type', 'application/json')
            cur.execute(
                "SELECT Id, Name, Priority, Priority < 2 AS Seated"
                " FROM CurrentPlayers JOIN Players ON PlayerId = Players.Id"
                " ORDER BY Seated DESC, Players.Name ASC")
            self.write(json.dumps(
                {"players":[dict(zip(["playerid", "name", "priority", "seated"],
                                     row))
                            for row in cur.fetchall()]}))


class MeetupOAuthAuthorize(handler.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        if meetup_ready():
            params = {
                "response_type":"code",
                "client_id":settings.MEETUP_CONSUMER_KEY,
                "redirect_uri":
                    "https://{}/seating/meetup/oauth_redirect".format(
                        self.request.host
                    ),
            }
            params = urllib.parse.urlencode(params)
            authorizeUrl = "https://secure.meetup.com/oauth2/authorize"
            return self.redirect(authorizeUrl + "?" + params)
        else:
            self.render("message.html",
                        message = "Meetup not configured",
                        title="Meetup not configured")

def FetchAccessToken(requestData, host):
    data = {
        "client_id":settings.MEETUP_CONSUMER_KEY,
        "client_secret":settings.MEETUP_CONSUMER_SECRET,
        "redirect_uri":
            "https://{}/seating/meetup/oauth_redirect".format(host),
    }
    data.update(requestData)

    url = "https://secure.meetup.com/oauth2/access"
    headers = {'User-Agent': settings.USER_AGENT}

    data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(url, data, headers)
    with urllib.request.urlopen(req) as response:
        accessResponse = response.read().decode('utf-8')

    # If our authorization response succeeded above
    if accessResponse is not None:
        try:
            return json.loads(accessResponse)
        except:
            message = "Couldn't parse meetup authorization response."
            if response is not None and 'error' in response:
                message += " Error: " + response['error']
            return {"message":message}
    else:
        return {"message":"No response received"}

class MeetupOAuthRedirect(handler.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        # Predefine responseData so the parsing code isn't nested so deeply
        responseData = None
        if meetup_ready():
            authCode = self.get_argument("code", None)
            if authCode is not None:
                response = FetchAccessToken(
                    {
                        "grant_type":"authorization_code",
                        "code":authCode,
                    },
                    self.request.host
                )
                if "access_token" in response:
                    self.set_secure_cookie(
                        "access_token",
                        str(response['access_token'])
                    )
                    self.set_secure_cookie(
                        "refresh_token",
                        str(response['refresh_token'])
                    )
                    CLOSE_TIMEOUT_SECONDS = 2
                    windowCloseScript = """
                        <script type="text/javascript">
                            $(function(){{ setTimeout(window.close, {}); }});
                        </script>
                    """.format(
                       CLOSE_TIMEOUT_SECONDS * 1000
                    )
                    return self.render("message.html",
                                message =
                                    "Authorization Success. " +
                                    "This window will close in {} seconds.".format(
                                    CLOSE_TIMEOUT_SECONDS
                                ),
                                head_html = windowCloseScript,
                                title="Meetup Authorization Success")
                elif "message" in response:
                    return self.render("message.html",
                                message = message,
                                title="Meetup Authorization Failure")
                else:
                    return self.render("message.html",
                                message = "Unknown Meetup Authorization Failure",
                                title="Meetup Authorization Failure")
            else:
                return self.redirect("/seating/meetup/oauth_authorize")
        else:
            return self.render("message.html",
                        message = "Meetup not configured",
                        title="Meetup not configured")


class AddMeetupPlayers(MeetupEventHandler):
    @tornado.web.authenticated
    def post(self):
        ret = {'status':'error',
                'type':'unknown',
                'message':'Unknown error ocurred'}
        if meetup_ready():
            access_token = self.get_secure_cookie("access_token", None)

            if access_token is None:
                return self.write(json.dumps({'status':'error',
                        'type':'not-authenticated',
                        'message':'No OAuth access token yet.'}))
            else:
                access_token = access_token.decode('ascii')

            event = None
            try:
                event = self.current_meetup_event()
            except Exception as e:
                return self.write(json.dumps({'status':'error',
                        'type':'query-exception',
                        'message':'Error ocurred querying meetup events, {}'
                       .format(e)}))
            if event is not None:
                rsvps = None
                try:
                    rsvps = make_meetup_request(
                        "/{}/events/{}/rsvps".format(
                            settings.MEETUP_GROUPNAME,
                            event['id']
                        ),
                        access_token,
                        {'response': 'yes'}
                    )
                    names = [rsvp['member']['name'] for rsvp in rsvps
                             if len(rsvp['member']['name']) > 1]
                except Exception as e:
                    ret = {'status':'error',
                           'message':'Error ocurred querying meetup RSVPs, {}'
                       .format(e)}
                    names = []
                if len(names) < (len(rsvps) if rsvps else 0):
                    log.info('In the Meetup on {}'
                             ' some RSVP names are too short: {}'.format(
                        datetime.date.fromtimestamp(event['time'] / 1000),
                        ', '.join("'{}'".format(rsvp['member']['name'])
                                  for rsvp in rsvps
                                  if len(rsvp['member']['name']) <= 1)))
                if len(names) > 0:
                    with db.getCur() as cur:
                        for name in names:
                            cur.execute(
                                "SELECT Id, PlayerId, MeetupName FROM Players"
                                "  LEFT OUTER JOIN CurrentPlayers ON"
                                "    Id = PlayerId"
                                "  WHERE COALESCE(MeetupName, Name) = ?",
                                (name,))
                            result = cur.fetchone()
                            if result is None or result[0] is None:
                                newCurrentPlayer(cur, name, status=2, meetupName=name)
                            elif result[1] is None:
                                newCurrentPlayer(cur, name, status=1,
                                                 meetupName=result[2])
                            else:
                                log.debug('Ignoring request to re-add {}'
                                          .format(name))
                    ret['status'] = "success"
                    ret['message'] = "Players added"
                    ret['names'] = names
        else:
            ret['message'] = 'Meetup.com API not configured'
        self.write(json.dumps(ret))

def newCurrentPlayer(cur, player, status=0, meetupName=None):
    sql = "SELECT Id FROM Players WHERE Id = ? OR Name = ?"
    bindings = (player, ) * 2
    if meetupName:
        sql += " OR MeetupName = ?"
        bindings += (meetupName,)
    cur.execute(sql, bindings)
    row = cur.fetchone()
    if row is None or len(row) == 0:
        if meetupName == '':
            meetupName = None
        cur.execute("INSERT INTO Players(Name, MeetupName) VALUES (?, ?)",
                    (player, meetupName))
        cur.execute("SELECT Id FROM Players WHERE Name = ?", (player,))
        row = cur.fetchone()
    player = row[0]
    cur.execute("INSERT INTO CurrentPlayers(PlayerId, Priority)"
                " SELECT ?, ? WHERE NOT EXISTS"
                "  (SELECT 1 FROM CurrentPlayers WHERE PlayerId = ?)",
                  (player, status, player))
    return True

class AddCurrentPlayer(handler.BaseHandler):
    @tornado.web.authenticated
    def post(self):
        player = self.get_argument('player', None)
        status =  self.get_argument('status', 1)

        ret = {'status':'error','message':'Unable to add new player'}

        if player is None or player == "":
            ret['message'] = "Please enter a player"
        with db.getCur() as cur:
            try:
                if newCurrentPlayer(cur, player, status=status):
                    ret['status'] = "success"
                    ret['message'] = "Player added"
            except:
                pass

        self.write(json.dumps(ret))

class RemovePlayer(handler.BaseHandler):
    @tornado.web.authenticated
    def post(self):
        player = self.get_argument('player', None)

        if player is None:
            self.write('{"status":1,"error":"Please enter a player"}')
            return

        with db.getCur() as cur:
            cur.execute("DELETE FROM CurrentPlayers WHERE PlayerId IN"
                        " (SELECT Id FROM Players WHERE Players.Id = ? OR"
                        "      Players.Name = ?)",
                        (player, player))
            self.write('{"status":0}')

class PrioritizePlayer(handler.BaseHandler):
    @tornado.web.authenticated
    def post(self):
        player = self.get_argument('player', None)
        priority = self.get_argument('priority', 0)

        if player is None:
            self.write('{"status":1,"error":"Please enter a player"}')
            return

        with db.getCur() as cur:
            cur.execute(
                "UPDATE CurrentPlayers Set Priority = ? WHERE PlayerId IN"
                " (SELECT Id FROM Players WHERE Players.Id = ? OR"
                " Players.Name = ?)",
                (priority, player, player))

            self.write('{"status":0}')

class ClearCurrentPlayers(handler.BaseHandler):
    @tornado.web.authenticated
    def post(self):
        with db.getCur() as cur:
            cur.execute("DELETE FROM CurrentPlayers")
            cur.execute("DELETE FROM CurrentTables")
            self.set_header('Content-Type', 'application/json')
            self.write('{"status":0}')

def getCurrentTables():
    tables = []
    with db.getCur() as cur:
        cur.execute("SELECT Players.Name FROM CurrentTables"
                    "  INNER JOIN Players"
                    "   ON Players.Id = CurrentTables.PlayerId")
        rows = cur.fetchall()
        numplayers = len(rows)
        total_tables = numplayers // 4
        extra_players = numplayers % 4
        if total_tables > 0 and extra_players <= total_tables:
            tables_4p = total_tables - extra_players
            places = "東南西北５"
            for table in range(total_tables):
                players = [{"wind": places[player],
                            "name": rows[table * 4 + max(0, table - tables_4p) +
                                         player][0]}
                           for player in range(4 if table < tables_4p else 5)]
                tables += [{"index": str(table + 1), "players": players}]
    return tables, numplayers

class CurrentTables(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'application/json')
        tables, numplayers = getCurrentTables()
        if len(tables) > 0:
            result = {"status": "success", "message": "Generated tables",
                      "tables": tables, "numplayers": numplayers}
        else:
            result = {"status":"error",
                      "message": "Invalid number of players, {}".format(
                          numplayers)}
        self.write(json.dumps(result))

class PlayersList(tornado.web.RequestHandler):
    def get(self):
        with db.getCur() as cur:
            self.set_header('Content-Type', 'application/json')
            cur.execute("SELECT Name FROM Players WHERE Id != ? ORDER BY Name",
                        (scores.getUnusedPointsPlayerID(),))
            self.write(json.dumps(list(map(lambda x:x[0], cur.fetchall()))))

class AddGameHandler(handler.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        tables, numplayers = getCurrentTables()
        unusedPointsIncrement, perPlayer = scores.getPointSettings()
        self.render("addgame.html", tables=tables,
                    unusedPointsIncrement=unusedPointsIncrement)

    @tornado.web.authenticated
    def post(self):
        self.write(json.dumps(scores.addGame(json.loads(
            self.get_argument('scores', None)))))

POPULATION = 256

def bestArrangement(tables, playergames, priorities, population = POPULATION):
    numplayers = len(tables)

    tabless = []
    for i in range(POPULATION):
        tables = tables[:]
        random.shuffle(tables)
        tabless += [(tablesScore(tables, playergames, priorities), tables)]
    tabless.sort(key=itemgetter(0))

    minScore = tabless[0][0]
    iteration = 0

    while iteration < numplayers and minScore > 0:
        for j in range(POPULATION):
            newTables = mutateTables(tabless[j][1])
            tabless += [(tablesScore(newTables, playergames, priorities), newTables)]
        tabless.sort(key=itemgetter(0))
        tabless = tabless[0:POPULATION]

        iteration += 1
        if minScore != tabless[0][0]:
            minScore = tabless[0][0]
            improved = 0

    return tabless[0][1]

def mutateTables(tables):
    tables = tables[:]
    a = random.randint(0, len(tables) - 1)
    b = random.randint(0, len(tables) - 1)
    tables[a], tables[b] = tables[b], tables[a]

    return tables

def tablesScore(players, playergames, priorities):
    numplayers = len(players)
    if numplayers >= 8:
        tables_5p = numplayers % 4
        total_tables = int(numplayers / 4)
        tables_4p = total_tables - tables_5p
    else:
        if numplayers >= 5:
            tables_5p = 1
        else:
            tables_5p = 0
        total_tables = 1
        tables_4p = total_tables - tables_5p

    score = 0

    for i in range(0, tables_4p * 4, 4):
        table = players[i:i+4]
        score += tableScore(table, playergames, priorities)

    for i in range(tables_4p * 4, numplayers, 5):
        table = players[i:i+5]
        score += tableScore(table, playergames, priorities)

    return score

def tableScore(players, playergames, priorities):
    numplayers = len(players)

    score = 0
    for i in range(numplayers):
        for j in range(i + 1, numplayers):
            if (players[i], players[j]) in playergames:
                score += playergames[(players[i], players[j])]
            elif (players[j], players[i]) in playergames:
                score += playergames[(players[j], players[i])]
        if priorities[players[i]] == 1 and numplayers == 5:
            score += 100
    return score

def playerGames(players, c):
    numplayers = len(players)

    playergames = dict()
    now = datetime.datetime.now()
    now = str(now.year) + " " + str(int((now.month - 1) / 3))

    for i in range(numplayers):
        for j in range(i + 1, numplayers):
            games = c.execute("SELECT COUNT(*) FROM Scores WHERE PlayerId = ? AND GameId IN (SELECT GameId FROM Scores WHERE PlayerId = ?) AND strftime('%Y', Date) || ' ' || ((strftime('%m', Date) - 1) / 3) = ?", (players[i], players[j], now)).fetchone()[0]
            if games != 0:
                playergames[(players[i], players[j])] = games

    return playergames
