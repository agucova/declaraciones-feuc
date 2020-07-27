import os
from declaraciones_feuc.model import db, Person, Statement, Organization
from declaraciones_feuc.auth import get_user_info, get_redirect_url
from oauthlib.oauth2 import WebApplicationClient
from flask import Flask
from flask import render_template, redirect, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

superusers = ["agucova@uc.cl", "mihenriquez@uc.cl", "ashasbun@uc.cl"]

# Initialize app
app = Flask(__name__)
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

db.create_tables(
    [Person, Statement, Organization]
)  # TODO: #3 Remove create_tables on request

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_person(id):
    return Person.get_or_none(id)


# DB connection per request
@app.before_request
def before_request():
    db.connect()
    if not current_user.is_authenticated:
        current_user.is_representative = False


# Disable cache and close db
@app.after_request
def after_request(response):
    db.close()
    return response


# Error pages
@app.errorhandler(404)
def page_not_found(e):
    return (
        render_template("404.html", user=current_user,),
        404,
    )


@app.errorhandler(403)
def page_forbidden(e):
    return (
        render_template("403.html", user=current_user,),
        403,
    )


@app.errorhandler(500)
def internal_server_error(e):
    return (
        render_template("500.html", user=current_user,),
        500,
    )


# Routes


@app.route("/")
def home():
    return render_template("home.html", user=current_user,)


@app.route("/declaraciones")
def declaraciones():
    return render_template("statements.html", user=current_user,)


@app.route("/representantes")
def representantes():
    return render_template("representatives.html", user=current_user,)


@app.route("/crear")
@login_required
def upload():
    if current_user.is_representative:
        return render_template("upload.html", user=current_user, use=["upload"],)
    else:
        return page_forbidden(403)


@app.route("/org")
@login_required
def organization():
    # Check if the user is in an organization
    if current_user.member_of:
        org = current_user.member_of
        return render_template("organization.html", user=current_user, org=org,)
    else:
        return page_forbidden(403)


@app.route("/miembros")
@login_required
def members():
    if current_user.member_of:
        org = current_user.member_of
        return render_template("members.html", user=current_user, org=org)
    else:
        return page_forbidden(403)


@app.route("/ajustes")
@login_required
def settings():
    # If the user is in an organization and is an admin
    if current_user.member_of and current_user.admin_of:
        org = current_user.member_of
        # If an user was not provided.
        if not (username_to_modify := request.args.get("usuario")):
            return render_template("settings.html", user=current_user, org=org)
        else:
            # split in case it also inputted the email
            username_to_modify = username_to_modify.split("@")[0]
            # retrieve user from db, if failed return error
            if not (
                user_to_modify := Person.get_or_none(
                    Person.username == username_to_modify
                )
            ):
                return render_template(
                    "settings.html",
                    user=current_user,
                    org=org,
                    get_flashed_messages=(
                        lambda: ["El usuario no está en la plataforma."]
                    ),
                )
            if request.args.get("añadir"):
                # if user is not already part of an org
                if not user_to_modify.member_of:
                    user_to_modify.member_of = org
                    user_to_modify.save()
                    print("user modified")
                    return render_template("settings.html", user=current_user, org=org)
                else:
                    return render_template(
                        "settings.html",
                        user=current_user,
                        org=org,
                        get_flashed_messages=(
                            lambda: ["El usuario ya pertenece a una organización."]
                        ),
                    )
                return render_template("settings.html", user=current_user, org=org)
            elif request.args.get("remover"):
                if user_to_modify.member_of == org:
                    user_to_modify.member_of = None
                    user_to_modify.save()
                    return render_template("settings.html", user=current_user, org=org)
                else:
                    return render_template(
                        "settings.html",
                        user=current_user,
                        org=org,
                        get_flashed_messages=(
                            lambda: ["El usuario no está en tu organización."]
                        ),
                    )
                return render_template("settings.html", user=current_user, org=org)
            else:
                return internal_server_error(500)
    else:
        return page_forbidden(403)


# Authentication and registration with Google


@login_manager.unauthorized_handler
def unauthorized():
    return page_forbidden(403)


@app.route("/login")
def login():
    return redirect(
        get_redirect_url(client=client, request=request, discovery=GOOGLE_DISCOVERY_URL)
    )


@app.route("/login/callback")
def callback():
    userinfo = get_user_info(
        client=client,
        request=request,
        client_id=GOOGLE_CLIENT_ID,
        secret=GOOGLE_CLIENT_SECRET,
        discovery=GOOGLE_DISCOVERY_URL,
    )

    # Check if the email is verified
    if userinfo.get("email_verified"):
        google_id = userinfo["sub"]
        email = userinfo["email"]
        first_name = (userinfo["given_name"],)
        last_name = userinfo["family_name"]
        name = userinfo["name"]
    else:
        return "Email no disponible o no verificado. ", 400

    # Doesn't exist? Add to database
    if not Person.select().where(Person.google_id == google_id).exists():
        username = email.split("@")[0]  # Extracts user from the first part of the email
        domain = email.split("@")[1]

        allowed_domains = [
            "uc.cl",
            "puc.cl",
            "mat.uc.cl",
            "ing.uc.cl",
            "ing.puc.cl",
            "mat.puc.cl",
        ]
        if not any(
            [domain == allowed_domain for allowed_domain in allowed_domains]
        ):  # Check if user is part of the university
            return page_forbidden(403)

        if email in superusers:  # Give superuser access
            cai = Organization.create(  # Add me in the CAi
                name="Centro de Alumnos de Ingeniería",
                acronym="CAi",
                type_of_org="Centro de Estudiantes",
            )

            Person.create(
                google_id=google_id,
                username=username,
                email=email,
                name=name,
                first_name=first_name,
                last_name=last_name,
                is_representative=True,
                is_active=True,
                is_authenticated=True,
                member_of=cai,
                admin_of=cai,
                is_superuser=True,
            )

        else:
            Person.create(
                google_id=google_id,
                username=username,
                email=email,
                name=name,
                first_name=first_name,
                last_name=last_name,
                is_representative=False,
                is_active=True,
                is_authenticated=True,
            )

    user = Person.get(Person.google_id == google_id)  # Fetch user

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("home"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(ssl_context=("cert.pem", "key.pem"))
