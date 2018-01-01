#!/usr/bin/env python3

import db
import util
import leaderboard
import settings

def updateGame(cur, gameid):
    cur.execute("SELECT PlayerId,RawScore,Chombos,Id,Date FROM Scores WHERE GameId = ? ORDER BY GameId", (gameid,))
    scores = []
    for row in cur.fetchall():
        scores += [{"player":row[0], "score": row[1], "chombos": row[2], "id": row[3], 'date': row[4]}]

    scores.sort(key=lambda x: x['score'], reverse=True)

    total = 0
    for score in scores:
        total += score['score']
    expectedtotal = len(scores) * settings.SCOREPERPLAYER
    if total != expectedtotal:
        print("Scores for game " + gameid + " do not add up to " +
              str(expectedtotal))
        return

    cur.execute("DELETE FROM Scores WHERE GameId = ?", (gameid,))
    for i in range(0, len(scores)):
        score = scores[i]

        # TODO: Fix this to use db.addGame for all the scores in the game
        adjscore = util.getScore(score['score'], len(scores), i + 1) - score['chombos'] * 8
        gamedate = score['date']

        cur.execute("INSERT INTO Scores(GameId, PlayerId, Rank, PlayerCount, RawScore, Chombos, Score, Date, Quarter) VALUES(?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y', ?) || ' ' || case ((strftime('%m', ?) - 1) / 3) when 0 then '1st' when 1 then '2nd' when 2 then '3rd' when 3 then '4th' end)", (gameid, score['player'], i + 1, len(scores), score['score'], score['chombos'], adjscore, gamedate, gamedate, gamedate))

        leaderboard.clearCache()

def main():
    with db.getCur() as cur:
        cur.execute("SELECT GameId FROM Scores WHERE Quarter = '2017 2nd' AND Chombos > 0")
        games = cur.fetchall()
        for game in games:
            updateGame(cur, game[0])


if __name__ == "__main__":
    main()
