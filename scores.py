#!/usr/bin/env python3

import json
import handler
import tornado.web
import datetime
import collections

import db
import settings
import leaderboard

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

def getScore(score, uma):
    return (score - settings.SCOREPERPLAYER) / 1000.0 + uma

dateFormat = "%Y-%m-%d"

def addGame(scores, gamedate = None, gameid = None):
    """Add or replace game scores for a particular game in the database.
    The scores should be a list of dictionaries.
    Each dictionary should have either a 'PlayerId' or 'Name',
    a raw 'Score', and a 'Chombos' count.
    One of the players may be the UnusedPointsPlayer to represent points
    that were not claimed at the end of play.
    The gamedate defaults to today.  A new gameid is created if none is given.
    If a player name is not found in database, a new record is created for
    them.
    Returns a dictionary with a 'status' and a 'message' field.  Status of 0
    means success.
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
    pointHistogram = collections.defaultdict(lambda : 0)
    for score in scores:
        isUnusedPlayerId = ('PlayerId' in score and
                            score['PlayerId'] in (-1, unusedPointsPlayerID))
        isUnusedPlayerName = ('Name' in score and
                              score['Name'] == unusedPointsPlayerName)
        score['points'] = score['Score'] - (
            settings.CHOMBOPENALTY * score['Chombos'] * 1000)
        if isUnusedPlayerName or isUnusedPlayerId:
            score['PlayerId'] = unusedPointsPlayerID
            score['Name'] = unusedPointsPlayerName
            hasUnusedPoints = True
            unusedPoints = score['Score']
        else:
            pointHistogram[score['points']] += 1
        uniqueIDs.add(score['Name'] if 'Name' in score else score['PlayerId'])
        total += score['Score']
        score['Date'] = gamedate

    realPlayerCount = len(scores) - (1 if hasUnusedPoints else 0)

    if not (4 <= realPlayerCount and realPlayerCount <= 5):
        return {"status":1, "error":"Please enter 4 or 5 scores"}

    if hasUnusedPoints and unusedPoints % unusedPointsIncrement() != 0:
        return {"status":1,
                "error":"Unused points must be a multiple of {0}".format(
                    unusedPointsIncrement())}

    if "" in uniqueIDs:
        return {"status":1, "error":"Please enter all player names"}

    if len(uniqueIDs) < len(scores):
        return {"status":1, "error": "All players must be distinct"}

    targetTotal = realPlayerCount * settings.SCOREPERPLAYER
    if total != targetTotal:
        return {"status": 1,
                "error": "Scores add up to {}, not {}".format(
                    total, targetTotal)}

    # Sort scores for ranking, ensuring unused points player is last, if present
    scores.sort(
        key=lambda x: ('PlayerId' not in x or x['PlayerId'] != unusedPointsPlayerID, x['points']),
        reverse=True)

    with db.getCur() as cur:
        if gameid is None:
            cur.execute("SELECT COALESCE(GameId, 0) FROM Scores ORDER BY GameId DESC LIMIT 1")
            gameid = cur.fetchone()[0] + 1
        else:
            cur.execute("DELETE FROM Scores WHERE GameId = ?", (gameid,))

        rank = 1
        pointHistogram[None] = 0
        last_points = None
        for score in scores:
            if score['points'] != last_points:
                rank += pointHistogram[last_points]
                last_points = score['points']
            score['rank'] = rank
            score['uma'] = 0
            if score.get('PlayerId', None) != unusedPointsPlayerID:
                for j in range(rank-1, rank-1 + pointHistogram[last_points]):
                    score['uma'] += umas[realPlayerCount][j]
                score['uma'] /= pointHistogram[last_points]
            if 'PlayerId' not in score:
                cur.execute("SELECT Id FROM Players WHERE Name = ?",
                            (score['Name'],))
                player = cur.fetchone()

                if player is not None and len(player) > 0:
                    score['PlayerId'] = player[0]
                else:
                    cur.execute("INSERT INTO Players(Name) VALUES(?)",
                                (score['Name'],))
                    score['PlayerId'] = cur.lastrowid
            score['Rating'] = playerRatingBeforeDate(score['PlayerId'], gamedate)

        for i, score in enumerate(scores):

            if score['PlayerId'] == unusedPointsPlayerID:
                adjscore = 0
                rating = 0
            else:
                adjscore = getScore(score['points'], score['uma'])
                rating = deltaRating(scores, i, realPlayerCount)

            cur.execute(
                "INSERT INTO Scores(GameId, PlayerId, Rank, PlayerCount, "
                " RawScore, Chombos, Score, Date, Quarter, DeltaRating) "
                " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (gameid, score['PlayerId'], score['rank'], realPlayerCount,
                 score['Score'], score['Chombos'], adjscore, gamedate, quarter,
                 rating))

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
        cur.execute("SELECT COALESCE(COUNT(*), 0) FROM Scores"
                    "  WHERE PlayerId = ? AND Date < ?",
                    (scores[rank]['PlayerId'], gamedate))
        gameCount = cur.fetchone()[0]
        adjPlayer = max(1 - (gameCount * 0.008), 0.2)

    return (scores[rank]['uma'] +
            adjEvent * (avgOppRating - scores[rank]['Rating'])
            / 40) * adjPlayer

def getScores(gameid):
    with db.getCur() as cur:
        columns = ["Id","PlayerId","Score","RawScore","Chombos","Date",
                   "DeltaRating","Rank"]
        cur.execute("SELECT {0} FROM Scores WHERE GameId = ?".format(
            ",".join(columns)), (gameid,))
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
