#!/usr/bin/env python3

import datetime
import re
from passlib.hash import pbkdf2_sha256
from functools import wraps
from flask import request, session, render_template, redirect, g, url_for

import db
import util

from MahjongSite import app

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'user' in session:
            return redirect(url_for('Login', next=request.path[1:]))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/invite', methods=["GET", "POST"])
@login_required
def Invite():
    if request.method == "GET":
        return render_template("invite.html")
    elif request.method == "POST":
        email = request.form['email']
        if not re.match("^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]+$", email, flags = re.IGNORECASE):
            return render_template("invite.html", message = "Please enter a valid email address.")
        else:
            with db.getCur() as cur:
                code = util.randString(32)
                cur.execute("INSERT INTO VerifyLinks (Id, Email, Expires) VALUES (?, LOWER(?), ?)", (code, email, (datetime.date.today() + datetime.timedelta(days=7)).isoformat()))

            util.sendEmail(email, "Your SeattleMahjong Account",
                    "<p>You've been invited to SeattleMahjong\n<br />\
                    Click <a href=\"" +  request.url_root + "verify/" + code + "\">this</a> link to accept the invite and register an account or copy and paste the following into your URL bar:<br />" +  request.url_root + "verify/" + code + "</p>\n" +
                    "<p>If you believe you received this email in error, it can be safely ignored. It is likely a user simply entered your email by mistake.</p>")

            return render_template("message.html", message = "Invite sent. It will expire in 7 days.", title = "Invite")

@app.route('/verify/<q>', methods=["GET", "POST"])
def VerifyHandler(q):
    if request.method == "GET":
        with db.getCur() as cur:
            cur.execute("SELECT Email FROM VerifyLinks WHERE Id = ? AND Expires > datetime('now')", (q,))

            if cur.rowcount == 0:
                    return redirect("/")

            email = cur.fetchone()[0]

        return render_template("verify.html", email = email, id = q)
    elif request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        vpassword = request.form['vpassword']

        if email is None or password is None or vpassword is None or email == "" or password == "" or vpassword == "":
            return render_template("verify.html", email = email, id = q, message = "You must enter an email, pasword, and repeat your password")
        if password != vpassword:
            return render_template("verify.html", email = email, id = q, message = "Your passwords didn't match")

        with db.getCur() as cur:
            passhash = pbkdf2_sha256.encrypt(password)

            cur.execute("INSERT INTO Users (Email, Password) VALUES (LOWER(?), ?)", (email, passhash))
            session["user"] = str(cur.lastrowid)
            cur.execute("DELETE FROM VerifyLinks WHERE Id = ?", (q,))

        return redirect("/")

@app.route('/reset', methods=['GET', 'POST'])
def Reset():
    if request.method == "GET":
        return render_template("forgotpassword.html")
    elif request.method == "POST":
        with db.getCur() as cur:
            email = request.form["email"]
            cur.execute("SELECT Id FROM Users WHERE Email = ?", (email,))
            row = cur.fetchone()
            if row is not None:
                code = util.randString(32)
                cur.execute("INSERT INTO ResetLinks(Id, User, Expires) VALUES (?, ?, ?)", (code, row[0], (datetime.date.today() + datetime.timedelta(days=7)).isoformat()))

                util.sendEmail(email, "Your SeattleMahjong Account",
                    "<p>Here's the link to reset your SeattleMahjong account password\n<br />\
                    Click <a href=\"" +  request.url_root + "reset/" + code + "\">this</a> link to reset your password or copy and paste the following into your URL bar:<br />" +  request.url_root + "reset/" + code + "</p>\n")
                return render_template("message.html", message = "Your password reset link has been sent")
            else:
                return render_template("message.html", message = "No accounts found associated with this email", email = email)

@app.route('/reset/<q>', methods=["GET", "POST"])
def ResetLink(q):
    if request.method == "GET":
        with db.getCur() as cur:
            cur.execute("SELECT Email FROM Users JOIN ResetLinks ON ResetLinks.User = Users.Id WHERE ResetLinks.Id = ?", (q,))
            row = cur.fetchone()
            if row is None:
                return render_template("message.html", message = "Link is either invalid or has expired. Please request a new one")
            else:
                return render_template("resetpassword.html", email = row[0], id = q)
    elif request.method == "POST":
        password = request.form['password']
        vpassword = request.form['vpassword']

        with db.getCur() as cur:
            cur.execute("SELECT Users.Id, Email FROM Users JOIN ResetLinks ON ResetLinks.User = Users.Id WHERE ResetLinks.Id = ?", (q,))
            row = cur.fetchone()
            if row is None:
                return render_template("message.html", message = "Link is either invalid or has expired. Please request a new one")
            else:
                id = row[0]
                email = row[1]
                if password is None or vpassword is None or password == "" or vpassword == "":
                    return render_template("resetpassword.html", email = email, id = q, message = "You must enter a pasword and repeat that password")
                if password != vpassword:
                    return render_template("resetpassword.html", email = email, id = q, message = "Your passwords didn't match")
                passhash = pbkdf2_sha256.encrypt(password)

                cur.execute("UPDATE Users SET Password = ? WHERE Id = ?", (passhash, id))
                cur.execute("DELETE FROM ResetLinks WHERE Id = ?", (q,))
                return render_template("message.html", message = "Your password has been reset. You may now <a href=\"/login\">Login</a>")

@app.route('/login/<path:next>', methods=['GET', 'POST'])
@app.route('/login/', methods=['GET', 'POST'])
def Login(next = ''):
    if request.method == "GET":
        if 'current_user' in session:
            return render_template("message.html", message = "You're already logged in, would you like to <a href=\"/logout\">Logout?</a>")

        return render_template("login.html", next = next)
    elif request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        if not email or not password or email == "" or password == "":
            return render_template("login.html", message = "Please enter an email and password")

        with db.getCur() as cur:
            cur.execute("SELECT Id, Password FROM Users WHERE Email = LOWER(?)", (email,))

            row = cur.fetchone()
            if row is not None:
                result = row[0]
                passhash = row[1]

                if pbkdf2_sha256.verify(password, passhash):
                    session["user"] = str(result)
                    cur.execute("SELECT EXISTS(SELECT * FROM Admins WHERE Id = ?)", (result,))
                    if cur.fetchone()[0] == 1:
                        session["admin"] = True

                    if result != None:
                        return redirect('/' + next)
        return render_template("login.html", message = "Incorrect email and password", next = next)

@app.route('/logout')
def Logout():
    session.pop("user", None)
    session.pop("admin", None)
    return redirect("/")
