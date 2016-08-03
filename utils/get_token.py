from flask import Flask, abort, request, url_for
from uuid import uuid4
import requests
import requests.auth
import argparse
from os import environ
import errno
import pprint

STATE = str(uuid4())
app = Flask(__name__)


@app.route("/")
def homepage():
    text = "<a href='%s'>Authenticate with reddit</a>"
    return text % make_authorization_url()


def make_authorization_url():
    params = {
        "client_id": app.config['APP_ID'],
        "response_type": "code",
        "state": STATE,
        "redirect_uri": url_for("reddit_callback", _external=True),
        "duration": "permanent",
        "scope": "history edit identity"}
    import urllib
    url = "https://ssl.reddit.com/api/v1/authorize?" + urllib.urlencode(params)
    return url


@app.route("/cb")
def reddit_callback():
    error = request.args.get("error", "")
    if error:
        return "Error: " + error
    code = request.args.get("code")
    state = request.args.get("state")
    if state != STATE:
        abort(403)
    # We'll change this next line in just a moment
    tokens = get_tokens(code)
    print pprint.pformat(tokens)
    return "<pre>%s</pre>" % pprint.pformat(tokens)


def get_tokens(code):
    client_auth = requests.auth.HTTPBasicAuth(app.config['APP_ID'],
                                              app.config['APP_SECRET'])
    post_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": url_for("reddit_callback", _external=True)
    }
    response = requests.post("https://ssl.reddit.com/api/v1/access_token",
                             auth=client_auth,
                             data=post_data)
    return response.json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-h", "--host", default="127.0.0.1")
    parser.add_argument("-p", "--port", type=int, default=6501)
    parser.add_argument("-I", "--app-id",
                        type=str,
                        default=environ.get("APP_ID", None))
    parser.add_argument("-S", "--app-secret",
                        type=str,
                        default=environ.get("APP_SECRET", None))
    args = parser.parse_args()
    if not all([args.app_id, args.app_secret]):
        print args
        exit(errno.EINVAL)

    app.config['APP_ID'] = args.app_id
    app.config['APP_SECRET'] = args.app_secret
    app.run(debug=True, host=args.host, port=args.port)
