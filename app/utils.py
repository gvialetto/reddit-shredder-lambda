import requests
import requests.auth
from time import sleep

_SHREDDITLAMBDAVERSION = 0.1


class handle_throttling(object):
    """
    Handle the reddit API throttling limits.

    By documentation (https://github.com/reddit/reddit/wiki/API#rules) we are
    we are throttled to 60 requests / ~1 min. In reality it seems taht the
    reddit servers throttle you at about 600 requests / ~10 min, which
    normally allows us to complete our work without issues (unless you have
    *a lot* of comments to delete...).
    """
    __STATE = {
        'remaining': 0,
        'to_cycle_end': None
    }

    def __init__(self, function, state=None):
        self.__function = function
        if state is None:
            state = handle_throttling.__STATE
        self.__st = handle_throttling.__STATE

    def __reset_cycle(self):
        # if this is None this is our first request and we can skip this
        if self.__st['to_cycle_end'] is not None:
            # we are in the cycle and we have still requests remaining.
            if self.__st['remaining'] > 0:
                return
            # we are in the cycle and we have no more requests remaining:
            # sleep until the end of the cycle and continue.
            if self.__st['remaining'] == 0:
                # the +1 actually ensures that we sleep long enough
                sleep(self.__st['to_cycle_end']+1)

    def __save_state(self, r):
        if 'X-Ratelimit-Reset' in r.headers:
            self.__st['to_cycle_end'] = int(r.headers['X-Ratelimit-Reset'])
        if 'X-Ratelimit-Remaining' in r.headers:
            # wrap the header first in a float() and then in an int(),
            # otherwise we'll get a ValueError exception...
            self.__st['remaining'] = int(float(
                r.headers['X-Ratelimit-Remaining']))

    def __call__(self, *args, **kwargs):
        self.__reset_cycle()
        r = self.__function(*args, **kwargs)
        self.__save_state(r)
        return r


@handle_throttling
def do_request(url, action=requests.get, access_token=None, *args, **kwargs):
    """
    Add our user agent (as required) to all requests done to the reddit API
    """
    default_headers = {
        "User-Agent": "ShredditLambda/{version}".format(
            version=_SHREDDITLAMBDAVERSION
        )
    }
    if access_token is not None:
        default_headers['Authorization'] = "bearer {}".format(access_token)
    if 'headers' in kwargs:
        kwargs['headers'].update(default_headers)
    else:
        kwargs['headers'] = default_headers
    if not url.startswith("https://"):
        url = "https://oauth.reddit.com{}".format(url)
    return action(url, *args, **kwargs)


def do_request_post(url, *args, **kwargs):
    """
    Utility function to do POSTs instead of GETs
    """
    return do_request(
        url=url,
        action=requests.post,
        *args,
        **kwargs)


def get_access_token(app_id, app_secret, refresh_token):
    """
    Using client_id, client_secret and a refresh_token, fetch a new
    access token.
    """
    client_auth = requests.auth.HTTPBasicAuth(app_id, app_secret)
    post_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response = do_request_post(
        url="https://ssl.reddit.com/api/v1/access_token",
        auth=client_auth,
        data=post_data)
    if response.status_code != requests.codes.ok:
        return None
    return response.json()['access_token']
