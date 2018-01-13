#!/usr/bin/env python3

import db
import util
import leaderboard
import scores

def updateGame(gameid):
    game = scores.getScores(gameid)

    unusedPointsPlayerID = scores.getUnusedPointsPlayerID()
    hasUnusedPoints = False
    for score in game:
        if score['PlayerId'] in (-1, unusedPointsPlayerID):
            hasUnusedPoints = True

    realPlayerCount = len(game) - (1 if hasUnusedPoints else 0)

    with db.getCur() as cur:
        print("Updating " + str(realPlayerCount) + " players in " + str(gameid))
        for rank in range(realPlayerCount):
            score = game[rank]
            score['DeltaRating'] = scores.deltaRating(game, rank, realPlayerCount)
            cur.execute("UPDATE Scores SET DeltaRating = ? WHERE Id = ?", (score['DeltaRating'], score['Id']))

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
