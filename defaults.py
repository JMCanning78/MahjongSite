#!/usr/bin/env python3

# LOCALE
CLUBCITY = "Seattle"
CLUBSTATE = "WA"
CLUBNAME = "{0} Richi Mahjong".format(CLUBCITY)

# DB
#  DBFILE is the name of the file that contains the scores and player database.
DBFILE = "scores.db"
DBBACKUPS = "backups"
DBDATEFORMAT = "%Y-%m-%d-%H-%M-%S"
MEMCACHE = ""

# PREFERENCES
#   DROPGAMES is the default number of games a player must complete in a
#   quarter in order to have the lowest score dropped from the average.
DROPGAMES = 9
#   MAXDROPGAMES is the maximum number of games a player can drop in a quarter
#   Note that the higher this number is, the longer it will take to generate the quarterly leaderboard
MAXDROPGAMES = 4
#   LINKVALIDDAYS is the number of days links for invitations and
#   password resets should remain valid.  They expire after LINKVALIDDAYS
#   has passed.
LINKVALIDDAYS = 7

# MEETUP interface
#   If the club uses the meetup.com site for players to RSVP for games,
#   filling in the values below will allow you to populate the seating based
#   on who RSVP'd.  This only works for players whose name on meetup.com
#   is exactly the same as how they registered on this mahjong site.
#   Leave these values blank if you don't use meetup.com
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
