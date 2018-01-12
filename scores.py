#!/usr/bin/env python3

import json
import handler
import tornado.web
import datetime

import db
import settings

umas = {4:[15,5,-5,-15],
        5:[15,5,0,-5,-15]}

def quarterString(time=None):
    """Return the string for the calendar quarter for the given datetime object.
    Time defaults to current time"""
    if time is None:
        time = datetime.datetime.now()
    return time.strftime("%Y ") + ["1st", "2nd", "3rd", "4th"][
        (time.month - 1) // 3]

def unusedPointsIncrement(quarter=None):
    """Get the UnusedPointsIncrement value for the given quarter.
    The quarter defaults to the most recent quarter in the database
    (but no later than today's date)."""
    if quarter is None:
        quarter = quarterString()
    try:
        with db.getCur() as cur:
            cur.execute("SELECT COALESCE(UnusedPointsIncrement,0) FROM Quarters"
                        " WHERE Quarter <= ? ORDER BY Quarter DESC"
                        " LIMIT 1",
                        (quarter,))
            increment = cur.fetchone()[0]
    except:
        increment = 0
    return increment

_unusedPointsPlayer = None
unusedPointsPlayerName = '!#*UnusedPointsPlayer*#!'

def getUnusedPointsPlayerID():
    """ Get the ID of the Players table entry that records unused points in
    games.  If an entry doesn't exist, create one."""
    global _unusedPointsPlayer, unusedPointsPlayerName
    if _unusedPointsPlayer:
        return _unusedPointsPlayer
    with db.getCur() as cur:
        cur.execute("SELECT Id from Players WHERE Name = ? AND"
                    " MeetupName IS NULL",
                    (unusedPointsPlayerName,))
        result = cur.fetchall()
        if len(result) > 1:
            raise Exception("More than 1 player defined for unused points")
        elif len(result) == 1:
            _unusedPointsPlayer = result[0][0]
        else:
            cur.execute("INSERT INTO Players (Name, MeetupName) VALUES (?, NULL)",
                        (unusedPointsPlayerName,))
            _unusedPointsPlayer = cur.lastrowid
    return _unusedPointsPlayer

def getScore(score, numplayers, rank):
    return score / 1000.0 - 25 + umas[numplayers][rank]

dateFormat = "%Y-%m-%d"

def addGame(scores, gamedate = None, gameid = None):
    """Add raw scores for a particular game to the database.
    The scores should be a list of dictionaries.
    Each dictionary should have a 'player' name or ID, a raw 'score', and
    a 'chombos' count.
    One of the players may be the UnusedPointsPlayer to represent points
    that were not claimed at the end of play.
    The gamedate defaults to today.  A new gameid is created if none is given.
    If a player name is not found in database, a new record is created for
    them.
    """
    global dateFormat, unusedPointsPlayerName
    if gamedate is None:
        gamedate = datetime.datetime.now().strftime(dateFormat)
        quarter = quarterString()
    else:
        quarter = quarterString(datetime.datetime.strptime(gamedate, dateFormat))

    if scores is None:
        return {"status":1, "error":"Please enter some scores"}

    hasUnusedPoints = False
    unusedPoints = 0
    unusedPointsPlayerID = getUnusedPointsPlayerID()
    total = 0
    uniqueIDs = set()
    for score in scores:
        if score['player'] in (
                -1, unusedPointsPlayerID, unusedPointsPlayerName):
            score['player'] = unusedPointsPlayerID
            hasUnusedPoints = True
            unusedPoints = score['score']
        uniqueIDs.add(score['player'])
        total += score['score']

    realPlayerCount = len(scores) - (1 if hasUnusedPoints else 0)

    if not (4 <= realPlayerCount and realPlayerCount <= 5):
        return {"status":1, "error":"Please enter 4 or 5 scores"}

    if hasUnusedPoints and unusedPoints % db.unusedPointsIncrement() != 0:
        return {"status":1,
                "error":"Unused points must be a multiple of {0}".format(
                    unusedPointsIncrement())}

    if "" in uniqueIDs:
        return {"status":1, "error":"Please enter all player names"}

    if len(uniqueIDs) < len(scores):
        return {"status":1, "error": "All players must be distinct"}

    targetTotal = realPlayerCount * 25000
    if total != targetTotal:
        return {"status": 1,
                "error": "Scores do not add up to " + str(targetTotal)}

    # Sort scores for ranking, ensuring unused points player is last, if present
    scores.sort(
        key=lambda x: (x['player'] != unusedPointsPlayerID, x['score']),
        reverse=True)

    with db.getCur() as cur:
        if gameid is None:
            cur.execute("SELECT COALESCE(GameId, 0) FROM Scores ORDER BY GameId DESC LIMIT 1")
            gameid = cur.fetchone()[0] + 1
        else:
            cur.execute("DELETE FROM Scores WHERE GameId = ?", (gameid,))

        for i in range(len(scores)):
            score = scores[i]
            cur.execute("SELECT Id FROM Players WHERE Id = ? OR Name = ?",
                        (score['player'], score['player']))
            player = cur.fetchone()
            if player is None or len(player) == 0:
                cur.execute("INSERT INTO Players(Name) VALUES(?)",
                            (score['player'],))
                cur.execute("SELECT Id FROM Players WHERE Name = ?",
                            (score['player'],))
                player = cur.fetchone()
            player = player[0]

            score['player'] = player
            score['rating'] = playerRatingBeforeDate(player, gamedate)

        for i in range(len(scores)):
            score = scores[i]
            rating = deltaRating(scores, i, realPlayerCount, gameid)

            adjscore = 0 if score['player'] == unusedPointsPlayerID else (
                getScore(score['score'], realPlayerCount, i) -
                        score['chombos'] * 8)

            cur.execute(
                "INSERT INTO Scores(GameId, PlayerId, Rank, PlayerCount, "
                " RawScore, Chombos, Score, Date, Quarter, DeltaRating) "
                " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (gameid, player, i + 1, len(scores),
                 score['score'], score['chombos'], adjscore, gamedate, quarter, rating))

            leaderboard.clearCache()
    return {"status":0}

adjEvent = 0.5

def playerRatingBeforeDate(playerId, gamedate):
    with db.getCur() as cur:
        cur.execute("SELECT COALESCE(SUM(DeltaRating), 0) + ? FROM Scores WHERE PlayerId = ? AND Date < ?;", (settings.DEFAULT_RATING, playerId, gamedate))
        return cur.fetchone() [0]
    return settings.DEFAULT_RATING

def deltaRating(scores, rank, realPlayerCount):
    gamedate = scores[0]['Date']

    totalOppRating = 0
    for i in range(realPlayerCount):
        score = scores[i]
        if 'Rating' not in score:
            score['Rating'] = playerRatingBeforeDate(score['PlayerId'], gamedate)
        if i != rank:
            totalOppRating += score['Rating']
    avgOppRating = totalOppRating / (realPlayerCount - 1)

    with db.getCur() as cur:
        cur.execute("SELECT COALESCE(COUNT(*), 0) FROM Scores WHERE PlayerId = ? AND Date < ?", (scores[rank]['PlayerId'], gamedate))
        gameCount = cur.fetchone()[0]
        adjPlayer = max(1 - (gameCount * 0.008), 0.2)

    return (umas[realPlayerCount][rank] + adjEvent * (avgOppRating - scores[rank]['Rating']) / 40) * adjPlayer

def getScores(gameid):
    with db.getCur() as cur:
        columns = ["Id","PlayerId","Score","RawScore","Chombos","Date","DeltaRating"]
        cur.execute("SELECT {0} FROM Scores WHERE GameId = ? ORDER BY GameId".format(",".join(columns)), (gameid,))
        scores = []
        for row in cur.fetchall():
            score = dict(zip(columns, row))
            scores += [score]
        return scores

class AddGameHandler(handler.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("addgame.html",
                    unusedPointsIncrement=unusedPointsIncrement())
    @tornado.web.authenticated
    def post(self):
        scores = self.get_argument('scores', None)

        scores = json.loads(scores)

        self.write(json.dumps(addGame(scores)))
