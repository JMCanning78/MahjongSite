#!/usr/bin/env python2.7

import db

def getScore(score, numplayers, rank):
    uma = (3 - rank) * 10
    if numplayers == 5:
        uma += 5
    return round(score, -3) / 1000 - 30 + uma

def main():
    with db.getCur() as cur:
        cur.execute("SELECT RawScore,NumPlayers,Rank,GameId,Id FROM Scores ORDER BY GameId ASC, Rank DESC")
        rows = cur.fetchall()
        currentscore = 0
        for row in rows:
            score = getScore(row[0], row[1], row[2])
            currentscore += score
            if row[2] == 1:
                if currentscore < 0:
                    score -= currentscore
                elif currentscore > 0:
                    cur.execute("UPDATE Scores SET Score = Score - ? WHERE GameId = ? AND Rank = NumPlayers", (currentscore, row[3]))
                currentscore = 0
            cur.execute("UPDATE Scores SET Score = ? WHERE Id = ?", (score, row[4]))

if __name__ == "__main__":
    main()
