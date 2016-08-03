from transitions import Machine
from datetime import timedelta, datetime
from .utils import do_request, do_request_post


class Shredder(object):
    states = [
        "empty",
        "filled",
        "done",
        "failed"
    ]

    transitions = [
        {
            "trigger": "fetch_comments",
            "source": "empty",
            "dest": "filled",
            "prepare": [
                "do_fetch_comments"
            ],
            "unless": [
                "has_failed"
            ]
        },
        {
            "trigger": "fetch_comments",
            "source": "empty",
            "dest": "failed",
            "conditions": [
                "has_failed"
            ]
        },
        {
            "trigger": "delete_comments",
            "source": "*",
            "dest": "done",
            "prepare": [
                "do_delete_comments"
            ]
        }
    ]

    def __init__(self, access_token):
        self.__token = access_token
        self.__comments = []
        self.__failed = False
        self.__machine = Machine(
            model=self,
            states=Shredder.states,
            transitions=Shredder.transitions,
            initial="empty",
            auto_transitions=False)

    def has_failed(self, *args, **kwargs):
        """
        Generic failure transition check
        """
        return self.__failed

    def __get_comments(self, comments_url, params):
        while True:
            r = do_request(url=comments_url,
                           params=params,
                           access_token=self.__token)
            data = r.json()['data']
            for comment in data['children']:
                yield comment['data']
            if data['after'] is None:
                break
            params['after'] = data['after']

    def do_fetch_comments(self):
        params = {
            "raw_json": 1
        }
        # Get user nickname, needed for the comments
        r = do_request("/api/v1/me", params=params, access_token=self.__token)
        self.__comments = list(
            self.__get_comments(
                "/user/{}/comments".format(r.json()['name']), params))

    def do_delete_comments(self, delta=timedelta(days=300)):
        now = datetime.now()
        for comment in self.__comments:
            created_time = datetime.fromtimestamp(int(comment['created_utc']))
            if now - delta > created_time:
                do_request_post(url="/api/del", data={"id": comment['name']},
                                access_token=self.__token)
