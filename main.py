from app import get_access_token, Shredder
from datetime import timedelta
import json


def main():
    with open("./config.json") as config_file:
        data = json.load(config_file)
    access_token = get_access_token(
        app_id=data['app_id'],
        app_secret=data['app_secret'],
        refresh_token=data['refresh_token'])
    shredder = Shredder(access_token=access_token)
    shredder.fetch_comments()
    if shredder.state != "failed":
        shredder.delete_comments(
            delta=timedelta(days=int(data['days'])))


def handle_lambda(event=None, context=None):
    main()

if __name__ == '__main__':
    main()
