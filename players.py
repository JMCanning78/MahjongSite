#!/usr/bin/env python3

import datetime
import collections
import json
import sys

import handler
import db
import settings
import scores

class PlayersHandler(handler.BaseHandler):
    def get(self):
        with db.getCur() as cur:
            playerFields = db.table_field_names('Players')
            cur.execute(("SELECT {}, QuarterId FROM Players"
                         " LEFT OUTER JOIN Memberships"
                         " ON Players.Id = Memberships.PlayerId"
                         " WHERE Id != ?"
                         " ORDER BY Name ASC, QuarterId ASC").format(
                             ', '.join(playerFields)),
                        (scores.getUnusedPointsPlayerID(),))
            rows = cur.fetchall()
            players = collections.OrderedDict({})
            last_player = None
            for row in rows:          # Build dictionary for each player
                if row[0] != last_player:
                    players[row[0]] = collections.defaultdict(
                        lambda: list(),
                        zip(playerFields, row))
                    last_player = row[0]
                memberQtr = row[len(playerFields)]
                if memberQtr is not None:  # Memberships is a list of qtrs
                    players[row[0]]['Memberships'].append(memberQtr)

            cur.execute("SELECT DISTINCT Quarter FROM Scores UNION"
                        " SELECT DISTINCT Quarter FROM Quarters"
                        " ORDER BY Quarter ASC")
            quarters = [row[0] for row in cur.fetchall()]
            initialQtrsShown = [scores.quarterString()]
            if initialQtrsShown[0] in quarters:
                index = quarters.index(initialQtrsShown[0])
                initialQtrsShown = quarters[index:
                                            index + settings.MEMBERSHIPQUARTERS]
            elif len(quarters) > 0:
                initialQtrsShown = quarters[- settings.MEMBERSHIPQUARTERS:]
            else:
                initialQtrsShown = []

        self.render("players.html",
                    message = "No players found" if len(rows) == 0 else "",
                    players=players, quarters=quarters,
                    visibleQtrs=initialQtrsShown)

    @handler.is_admin
    def post(self):
        operation = self.get_argument('operation', None)
        playerId = self.get_argument('playerId', None)
        quarter = self.get_argument('quarter', None)
        value = self.get_argument('value', None)

        if not (operation in ['set_Name', 'set_MeetupName', 'set_Membership']
                and playerId is not None and value is not None):
            self.write(json.dumps({
                'status':'error',
                'message':'Invalid operation requested. {}'.format(
                    self.request.arguments)}))
            return

        with db.getCur() as cur:
            args = (value, playerId)
            if operation == 'set_Name':
                if not value:
                    self.write(json.dumps({
                        'status': 'error',
                        'message': 'Name cannot be empty'}))
                    return
                cur.execute('SELECT Id FROM Players WHERE Name = ?', (value,))
                result = cur.fetchall()
                if result and str(result[0][0]) != playerId:
                    self.write(json.dumps({
                        'status': 'error',
                        'message': 'Name "{}" matches {} other player{}'.format(
                            value, len(result), '' if len(result) == 1 else 's')}))
                    return
                sql = "UPDATE Players SET Name = ? WHERE Id = ?"
            elif operation == 'set_MeetupName':
                if value:
                    cur.execute('SELECT Id FROM Players WHERE MeetupName = ?',
                                (value,))
                    result = cur.fetchall()
                    if result and str(result[0][0]) != playerId:
                        self.write(json.dumps({
                            'status': 'error',
                            'message': 'Meetup Name "{}" matches {} other player{}'.format(
                                value, len(result),
                                '' if len(result) == 1 else 's')}))
                        return
                sql = "UPDATE Players SET MeetupName = ? WHERE Id = ?"
            elif operation == 'set_Membership':
                if quarter is None:
                    self.write(json.dumps({
                        'status': 'error',
                        'message': 'No quarter specified in membership update'}))
                    return
                if value == 'true':
                    sql = ("INSERT INTO Memberships (PlayerId, QuarterID)"
                           " VALUES (?, ?)")
                else:
                    sql = ("DELETE FROM Memberships "
                           "WHERE PlayerId = ? AND QuarterId = ?")
                args = (playerId, quarter)
            try:
                cur.execute(sql, args)
            except Exception as e:
                print(e, file=sys.stderr)
                self.write(json.dumps({'status': 'error', 'message': str(e)}))
                return
                
        self.write('{"status":0}')
