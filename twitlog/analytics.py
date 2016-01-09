import json
import os

from requests import Session
from BeautifulSoup import BeautifulSoup

from .cli import BaseCommand


class AnalyticsCommand(BaseCommand):

    def add_arguments(self):
        self.parser.add_argument('-x', '--no-tweets', action='store_true')
        self.parser.add_argument('-X', '--no-analytics', action='store_true')

    def main(self, args):
        if not self.args.no_tweets:
            self.update_tweets()
        if not self.args.no_analytics:
            self.update_analytics()

    def update_tweets(self):
        with self.db.connect() as con:
            params = {
                'screen_name': self.args.username,
                'trim_user': 'true', # We don't need full user objects
                'count': '200',
                'include_rts': 'false', # We don't want retweets
            }
            row = con.execute('SELECT max(id) FROM tweets').fetchone()
            if row:
                params['since_id'] = row[0]

            for tweet in self.oath.get_json('statuses/user_timeline', params=params):
                con.insert('tweets', {
                    'id': tweet['id'],
                    'json': json.dumps(tweet, sort_keys=True),
                })

    def update_analytics(self):

        session = Session()

        if 'TWITLOG_COOKIES' in os.environ:
            cookies = json.loads(os.environ['TWITLOG_COOKIES'])
            session.cookies.update(cookies)

        else:

            print 'Fetching homepage for auth token'
            res = session.get('https://twitter.com')

            body = BeautifulSoup(res.text)
            input_ = body.find(lambda tag: tag.name == 'input' and tag.get('name') == 'authenticity_token')
            authe_token = input_['value']


            print 'Logging into account'
            res = session.post('https://twitter.com/sessions', data={
                'session[username_or_email]': self.args.username,
                'session[password]': self.args.password,
                'return_to_ssl': 'true',
                'scribe_log': '',
                'redirect_after_login': '/',
                'authenticity_token': authe_token,
            })

            cookies = dict(session.cookies.iteritems())
            print
            print 'export TWITLOG_COOKIES=\'%s\'' % json.dumps(cookies)
            print

        with self.db.connect() as con:
            for tid, old_json in con.execute('''
                SELECT tweet.id, last.json
                FROM tweets as tweet
                LEFT JOIN tweet_metrics as last
                ON tweet.last_metrics_id = last.id
            '''):
                res = session.get('https://twitter.com/i/tfb/v1/tweet_activity/web/poll/%s' % tid)
                new_metrics = {k: int(v) for k, v in res.json()['metrics']['all'].iteritems()}
                print tid, new_metrics

                new_json = json.dumps(new_metrics, sort_keys=True)
                if old_json != new_json:
                    mid = con.insert('tweet_metrics', {
                        'tweet_id': tid,
                        'json': new_json,
                    })
                    con.update('tweets', {'last_metrics_id': mid}, {'id': tid})
                    con.commit()


