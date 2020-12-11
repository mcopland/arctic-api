import models.animals
import models.icebergs
import models.users

from constants import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE, USERS
from flask import Flask, render_template, request
from google.auth.transport import requests
from google.cloud import datastore
from google.oauth2 import id_token
from requests_oauthlib import OAuth2Session


# This disables the requirement to use HTTPS so that you can test locally.
import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = '1'

app = Flask(__name__)
app.register_blueprint(models.animals.bp)
app.register_blueprint(models.icebergs.bp)
app.register_blueprint(models.users.bp)

client = datastore.Client()
oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)


@app.route('/')
def index():
    authorization_url, state = oauth.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        # access_type and prompt are Google specific parameters
        access_type="offline", prompt="select_account")
    return render_template("/views/login.html", oauth_link=authorization_url)


# Users are redirected here and JWT is collected for future requests
@app.route("/oauth")
def oauthroute():
    token = oauth.fetch_token(
        "https://accounts.google.com/o/oauth2/token",
        authorization_response=request.url,
        client_secret=CLIENT_SECRET)

    # User information
    jwt = token["id_token"]
    req = requests.Request()
    id_info = id_token.verify_oauth2_token(jwt, req, CLIENT_ID)
    user_id = id_info["sub"]

    query = client.query(kind=USERS)
    results = list(query.fetch())

    # Search for User
    user_exists = False
    for u in results:
        if u["id"] == user_id:
            user_exists = True
            break

    # Update User
    if not user_exists:
        user = datastore.Entity(key=client.key(USERS))
        user.update({"id": user_id})
        client.put(user)

    return render_template("/views/user.html",
                           user_id=user_id, user_jwt=jwt)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081, debug=True)
