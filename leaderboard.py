#!/usr/bin/env python3

import json
import collections

import db
import handler
import settings
import scores

LBDcolumns = [col for col in db.table_field_names('Leaderboards')
              if col not in ['Place']]
periods = {
    "annual":{
        "queries":["""SELECT
            'annual',
             {datefmt},
             PlayerId,
             ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100)
               / 100 AS AvgScore,
             COUNT(Scores.Score) AS GameCount,
             0,
             COUNT(DISTINCT Date) AS DateCount
           FROM Scores
           WHERE PlayerId != ?
           AND {datetest}
           GROUP BY {datefmt},PlayerId
           ORDER BY AvgScore DESC;"""],
       "datefmt": "strftime('%Y', {date})",
       },
    "biannual":{
        "queries":["""SELECT
            'biannual',
             {datefmt},
             PlayerId,
             ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100)
               / 100 AS AvgScore,
             COUNT(Scores.Score) AS GameCount,
             0,
             COUNT(DISTINCT Date) AS DateCount
           FROM Scores
           WHERE PlayerId != ?
           AND {datetest}
        GROUP BY {datefmt},PlayerId
        ORDER BY AvgScore DESC;"""],
        "datefmt":"""strftime('%Y', {date}) || ' ' ||
               case ((strftime('%m', {date}) - 1) / 6)
                   when 0 then '1st'
                   when 1 then '2nd'
                end"""
    },
    "quarter":{
        "queries":["""SELECT
            'quarter',
             Scores.Quarter,
             PlayerId,
             ROUND(SUM(Scores.Score) * 1.0 / COUNT(Scores.Score) * 100)
               / 100 AS AvgScore,
             COUNT(Scores.Score) AS GameCount,
             COUNT(Scores.Score) / COALESCE(Quarters.GameCount, {DEFDROPGAMES}) AS DropGames,
             COUNT(DISTINCT Date) AS DateCount
           FROM Scores
             LEFT OUTER JOIN Quarters ON Scores.Quarter = Quarters.Quarter
           WHERE PlayerId != ? AND {{datetest}}
           GROUP BY Scores.Quarter,PlayerId
           ORDER BY AvgScore DESC;""".format(DEFDROPGAMES=settings.DROPGAMECOUNT)
        ],
        "datefmt": """strftime('%Y', {date}) || ' ' ||
               case ((strftime('%m', {date}) - 1) / 3)
                   when 0 then '1st'
                   when 1 then '2nd'
                   when 2 then '3rd'
                   when 3 then '4th'
                end"""
        }
}

def get_eligible(quarter=None):
    """Return a nested dictionary structure indexed by quarter and player ID
    that returns a dictionary with the following flags:
    'Member' for whether they were a member that quarter, 
    'Played' for whether they played any games that quarter, and
    'Eligible' indicating whether or not the player qualified for the
       end-of-quarter tournament in that quarter.
    """
    eligible = collections.defaultdict(
        lambda: collections.defaultdict(
            lambda: collections.defaultdict(lambda: False)))
    with db.getCur() as cur:
        cur.execute(
            "SELECT Scores.Quarter AS Qtr, Scores.PlayerId AS Plr,"
            "       QualifyingGames, QualifyingDistinctDates, COUNT(Score), "
            "       COUNT(DISTINCT Date), Memberships.QuarterId IS NOT NULL"
            " FROM Scores LEFT OUTER JOIN Quarters ON"
            "   Scores.Quarter = Quarters.Quarter"
            "   LEFT OUTER JOIN Memberships ON"
            "        Scores.PlayerId = Memberships.PlayerID AND"
            "        Scores.Quarter = Memberships.QuarterId"
            " WHERE Scores.PlayerId != ?"
            " GROUP BY Qtr, Plr "
            "UNION SELECT Quarters.Quarter AS Qtr, Players.Id Plr,"
            "       QualifyingGames, QualifyingDistinctDates, 0, 0,"
            "       Memberships.QuarterId IS NOT NULL"
            " FROM Quarters LEFT OUTER JOIN Players"
            "   LEFT OUTER JOIN Memberships ON"
            "        Players.Id = Memberships.PlayerID AND"
            "        Quarters.Quarter = Memberships.QuarterId"
            " WHERE Players.Id != ?"
            " ORDER BY Qtr, Plr",
            (scores.getUnusedPointsPlayerID(), scores.getUnusedPointsPlayerID()))
        rows = cur.fetchall()
    previousQtr = None
    for row in rows:
        Quarter, PlayerId, QGames, QDistinctDates, Games, Dates, Memb = row
        if Quarter not in eligible:
            if previousQtr is None:
                eligible[Quarter]['QGames'] = (
                    QGames or settings.QUALIFYINGGAMES)
                eligible[Quarter]['QDistinctDates'] = (
                    QDistinctDates or settings.QUALIFYINGDISTINCTDATES)
            else:
                eligible[Quarter]['QGames'] = (
                    QGames or eligible[previousQtr]['QGames'])
                eligible[Quarter]['QDistinctDates'] = (
                    QDistinctDates or eligible[previousQtr]['QDistinctDates'])
        previousQtr = Quarter
        eligible[Quarter][PlayerId]['Member'] = Memb
        eligible[Quarter][PlayerId]['Played'] = Games > 0
        eligible[Quarter][PlayerId]['Eligible'] = Memb and (
            Games >= eligible[Quarter]['QGames'] or
            Dates >= eligible[Quarter]['QDistinctDates'])
    return eligible
                    
class LeaderboardHandler(handler.BaseHandler):
    def get(self, period):
        self.render("leaderboard.html")

class LeaderDataHandler(handler.BaseHandler):
    def get(self, period):
        while period.startswith('/'):
            period = period[1:]
        if '/' in period:
            period, rest = period.split('/', 1)
        if period not in periods:
            period = "quarter"

        rows = []
        with db.getCur() as cur:
            displaycols = ['Name', 'Place'] + LBDcolumns
            cur.execute(
                ("SELECT {columns} FROM Leaderboards"
                 " JOIN Players ON PlayerId = Players.Id"
                 " WHERE Period = ? ORDER BY Date DESC, Place ASC").format(
                     columns=",".join(displaycols)),
                (period,)
            )
            rows = [dict(zip(displaycols, row)) for row in cur.fetchall()]

        eligible = get_eligible()

        leaderboards = collections.defaultdict(lambda: [])
        for row in rows:
            date = row['Date']
            for flag in ['Member', 'Eligible']:
                row[flag] = (row['Period'] == 'quarter' and
                             eligible[date][row['PlayerId']][flag])
            leaderboards[date].append(row)

        leaderboards = [
            {'Date': date, 'Board': board}
            for date, board in sorted(leaderboards.items(), reverse=True)]

        self.write(json.dumps({'leaderboards':list(leaderboards)}))

def genLeaderboard(leaderDate = None):
    """Recalculates the leaderboard for the given datetime object.
    If leaderDate is None, then recalculates all leaderboards."""
    with db.getCur() as cur:
        leadercols = ['Place'] + LBDcolumns
        leaderrows = []

        for periodname, period in periods.items():
            rows = []
            queries = period['queries']
            datefmt = period['datefmt']
            bindings = []
            if leaderDate is not None:
                datetest = "(" + datefmt + ") = (" + datefmt.format(date="?") + ")"
                bindings = [leaderDate] * datefmt.count("{date}")

            cur.execute("DELETE FROM Leaderboards WHERE Period = ? AND Date = {datefmt}".format(datefmt=datefmt.format(date="?")), [periodname] + bindings)

            for query in queries:
                cur.execute(query.format(datetest=datetest, datefmt=datefmt)
                            .format(date="Scores.Date"),
                            [scores.getUnusedPointsPlayerID()] + bindings)
                for row in cur.fetchall():
                    record = dict(zip(LBDcolumns, row))
                    # For Quarterly Leaderboards, compute dropped game average
                    if periodname == 'quarter' and int(record['DropGames']) > 0:
                        record['DropGames'] = min(settings.MAXDROPGAMES, 
                                                  record['DropGames'])
                        cur.execute(
                            "SELECT Score FROM Scores"
                            "  WHERE PlayerId = ? AND Quarter = ?"
                            "  ORDER BY Score ASC LIMIT -1 OFFSET ?",
                            (record['PlayerId'], record['Date'], 
                             record['DropGames']))
                        total = 0.0
                        count = 0
                        for score in cur.fetchall():
                            total += score[0]
                            count += 1
                        if count > 0:
                            record['AvgScore'] = round(total / count, 2)
                        record['GameCount'] -= record['DropGames']
                    rows += [record]

            rows.sort(key=lambda row: row['AvgScore'], reverse=True) # sort by score
            places = {}
            for row in rows:
                if row['Date'] not in places:
                    places[row['Date']] = 1
                row['Place'] = places[row['Date']]
                places[row['Date']] += 1

                leaderrow = [row[col] for col in leadercols]
                leaderrows += [leaderrow]

        query = "INSERT INTO Leaderboards({columns}) VALUES({colvals})".format(
                columns=",".join(leadercols),
                colvals=",".join(["?"] * len(leadercols))
            )
        cur.executemany(query, leaderrows)
