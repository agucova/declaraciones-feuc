from flask import Flask
from flask import render_template, redirect, request, url_for

from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from oauthlib.oauth2 import WebApplicationClient
import os
import requests
import json

from declaraciones_feuc.model import db, Person, Statement

app = Flask(__name__, instance_relative_config=True)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)


# Auth setup
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# OAuth2 Client
client = WebApplicationClient(GOOGLE_CLIENT_ID)


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_person(id):
    return Person.get(id)


# DB connection per request
@app.before_request
def before_request():
    db.connect()
    db.create_tables([Person, Statement])  # Performance hog, please remove


@app.after_request
def after_request(response):
    db.close()
    return response


# disable cache
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.errorhandler(404)
def page_not_found(e):
    return (
        render_template("404.html", is_authenticated=current_user.is_authenticated),
        404,
    )


@app.errorhandler(403)
def page_forbidden(e):
    return (
        render_template("403.html", is_authenticated=current_user.is_authenticated),
        403,
    )


@app.errorhandler(500)
def internal_server_error(e):
    return (
        render_template("500.html", is_authenticated=current_user.is_authenticated),
        500,
    )


@app.route("/")
def home():
    return render_template("home.html", is_authenticated=current_user.is_authenticated)


@app.route("/declaraciones")
def declaraciones():
    return render_template(
        "declaraciones.html", is_authenticated=current_user.is_authenticated
    )


@app.route("/representantes")
def representantes():
    return render_template(
        "representantes.html", is_authenticated=current_user.is_authenticated
    )


@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html", is_authenticated=current_user.is_authenticated)


# Here comes the auth


@login_manager.unauthorized_handler
def unauthorized():
    return page_forbidden(403)


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        print(userinfo_response.json())
        google_id = userinfo_response.json()["sub"]
        email = userinfo_response.json()["email"]
        first_name = (userinfo_response.json()["given_name"],)
        last_name = userinfo_response.json()["family_name"]
        name = userinfo_response.json()["name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Doesn't exist? Add to database
    if not Person.select().where(Person.google_id == google_id).exists():
        Person.create(
            google_id=google_id,
            username=email.split("@")[0],
            email=email,
            name=name,
            first_name=first_name,
            last_name=last_name,
            isRepresentative=False,
            is_active=True,
            is_authenticated=True,
        )

    user = Person.get(Person.google_id == google_id)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("home"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


if __name__ == "__main__":
    app.run(ssl_context=("cert.pem", "key.pem"))
