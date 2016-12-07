#!/usr/bin/env python3

import db

def getScore(score, numplayers, rank):
    uma = (3 - rank) * 10
    if numplayers == 5:
        uma += 5
    return score / 1000.0 - 30 + uma

def main():
    with db.getCur() as cur:
        cur.execute("SELECT RawScore,PlayerCount,Rank,GameId,Id FROM Scores WHERE RawScore != 0 AND Date BETWEEN '2015-01-01' AND '2015-12-31' ORDER BY GameId ASC, Rank DESC")
        rows = cur.fetchall()
        currentscore = 0
        for row in rows:
            score = getScore(row[0], row[1], row[2])
            currentscore += score
            if row[2] == 1:
                if currentscore != 0:
                    score -= currentscore
                currentscore = 0
            cur.execute("UPDATE Scores SET Score = ? WHERE Id = ?", (score, row[4]))

if __name__ == "__main__":
    main()
