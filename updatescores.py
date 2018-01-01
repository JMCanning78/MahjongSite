#!/usr/bin/env python3

import db
import util
import leaderboard
import scores
import settings

def updateGame(gameid):
    game = scores.getScores(gameid)

    unusedPointsPlayerID = scores.getUnusedPointsPlayerID()
    hasUnusedPoints = False
    total = 0
    for score in game:
        if score['PlayerId'] in (-1, unusedPointsPlayerID):
            hasUnusedPoints = True
        total += score['score']

    realPlayerCount = len(game) - (1 if hasUnusedPoints else 0)

    expectedtotal = len(scores) * settings.SCOREPERPLAYER
    if total != expectedtotal:
        print("Scores for game {} add up to {}, not {}".format(
            gameid, total, expectedtotal))
        return

    with db.getCur() as cur:
        print("Updating " + str(realPlayerCount) + " players in " + str(gameid))
        for rank in range(realPlayerCount):
            score = game[rank]
            score['DeltaRating'] = scores.deltaRating(game, rank, realPlayerCount)
            cur.execute("UPDATE Scores SET DeltaRating = ? WHERE Id = ?", (score['DeltaRating'], score['Id']))

    cur.execute("DELETE FROM Scores WHERE GameId = ?", (gameid,))
    for i, score in enumerate(game):

        # TODO: Fix this to use db.addGame for all the scores in the game
        adjscore = util.getScore(score['score'], len(scores), i + 1) - score['chombos'] * 8
        gamedate = score['date']

        cur.execute("INSERT INTO Scores(GameId, PlayerId, Rank, PlayerCount, RawScore, Chombos, Score, Date, Quarter) VALUES(?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y', ?) || ' ' || case ((strftime('%m', ?) - 1) / 3) when 0 then '1st' when 1 then '2nd' when 2 then '3rd' when 3 then '4th' end)", (gameid, score['player'], i + 1, len(scores), score['score'], score['chombos'], adjscore, gamedate, gamedate, gamedate))

    return game

def main():
    with db.getCur() as cur:
        cur.execute("SELECT DISTINCT GameId FROM Scores ORDER BY Date ASC")
        games = cur.fetchall()

    for game in games:
        gameid = game[0]
        updateGame(gameid)


if __name__ == "__main__":
    main()
