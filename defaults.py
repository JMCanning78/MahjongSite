#!/usr/bin/env python3

# LOCALE
CLUBCITY = "Seattle"
CLUBSTATE = "WA"
CLUBNAME = "{0} Riichi Mahjong".format(CLUBCITY)

# Sponsor linked web site - Link for upper left corner 'sponsor' logo
SPONSORLINK = "https://seattlemahjong.com"

# DB
#   DBFILE is the name of the file that contains the scores and player
#   database.
DBFILE = "scores.db"
#   DBBACKUPS is the name of a directory where backups of the scores
#   database will be stored.  Backups are made after significant changes
#   so that previous states can be recovered.
DBBACKUPS = "backups"
#   DBDATEFORMAT is datetime format string to use in naming the database
#   backup files with their timestamp
DBDATEFORMAT = "%Y-%m-%d-%H-%M-%S"

# PREFERENCES
# Game play related (some of these are settable for each quarter)
#   DROPGAMECOUNT is the default number of games a player must complete in a
#   quarter in order to have their lowest score dropped from the average.
#   For each DROPGAMECOUNT games played, one low score is dropped (e.g. if it
#   is 9 and the player completed 18 games, their 2 lowest scores are dropped)
DROPGAMECOUNT = 9
#   MAXDROPGAMES is the maximum number of games a player can drop in a quarter.
#   Quarters are typically 13 weeks.
MAXDROPGAMES = 3
#   DEFAULT_RATING is the starting rating for players with no games
DEFAULT_RATING = 1200
#   SCOREPERPLAYER sets the initial score each player has at the start of
#   each round.  It is used to determine what the total raw scores should
#   sum to at the end of each round and how to calculate points from those
#   sums
SCOREPERPLAYER = 25000
#   CHOMBOPENALTY is the number of points deducted for a chombo (error).  This
#   is counted in normalized points, e.g. a score of 8000 counts as 8 points
CHOMBOPENALTY = 8
#   UNUSEDPOINTSINCREMENT is the minimum amount of points that can be left
#   as unused at the end of a game.  Typically this is one riichi bet.
#   Unused points must be multiples of this amount.
UNUSEDPOINTSINCREMENT = 1000
#   QUALIFYINGGAMES is the minimum number of games a player must complete
#   in a quarter to qualify for the end-of-quarter tournament.
QUALIFYINGGAMES = 8
#   QUALIFYINGDISTINCTDATES is the minimum number of distinct dates of
#   play that a player must complete in a quarter to qualify for the
#   end-of-quarter tournament.
QUALIFYINGDISTINCTDATES = 8

# Adminstrative
#   FORECASTQUARTERS is the number of quarters ahead of the current quarter
#   to show in the Quarters Management dialog
FORECASTQUARTERS = 3
#   MEMBERSHIPQUARTERS is the initial number of quarters to show in the
#   Players dialog starting with the current quarter.
MEMBERSHIPQUARTERS = 4
#   TIMELINEQUARTERS is the max number of the most recent quarters to show in
#   the Player Statistics quarterly timeline.
TIMELINEQUARTERS = 12

# MEETUP interface
#   If the club uses the meetup.com site for players to RSVP for games,
#   filling in the values below will allow you to populate the seating based
#   on who RSVP'd.  Leave these values blank if you don't use meetup.com
#   MEETUP_APIKEY can be obtained from https://secure.meetup.com/meetup_api/key/
MEETUP_APIKEY = ""
#   MEETUP_GROUPNAME can be obtained from the URL you use to view your group
#   on meetup.com.  For example, the groupname from
#   https://www.meetup.com/MyMahjongClub/ is MyMahjongClub
MEETUP_GROUPNAME = ""

# EMAIL
#   These settings are for the outbound email server that sends invites
#   and password reset links to users.
EMAILSERVER = "smtp.server.com"
EMAILPORT = 587
EMAILUSER = "email@address.com"
EMAILFROM = "{0} <{1}>".format(CLUBNAME, EMAILUSER)
EMAILPASSWORD = ""
#   LINKVALIDDAYS is the number of days links for invitations and
#   password resets should remain valid.  They expire after LINKVALIDDAYS
#   has passed.
LINKVALIDDAYS = 7
