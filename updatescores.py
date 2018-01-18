#!/usr/bin/env python3

import db
import util
import leaderboard
import scores
import settings

def updateGame(gameid):
    print("Updating game", gameid)
    game = scores.getScores(gameid)
    status = scores.addGame(game)
    if status['status'] != 0:
        print(status)
    return game

def main():
    with db.getCur() as cur:
        cur.execute("SELECT DISTINCT GameId FROM Scores WHERE RawScore != 0 ORDER BY Date ASC")
        games = cur.fetchall()

    for game in games:
        gameid = game[0]
        updateGame(gameid)


if __name__ == "__main__":
    main()
