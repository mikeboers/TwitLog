import argparse
import os

from .database import Database


class BaseCommand(object):

    @classmethod
    def make_and_run(cls, argv=None):
        self = cls()
        return self.run(argv)

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.add_base_arguments()
        self.add_arguments()

    def add_base_arguments(self):
        for name in 'username', 'password', 'client-key', 'client-secret', 'owner-key', 'owner-secret':
            default = os.environ.get('TWITLOG_' + name.replace('-', '_').upper())
            self.parser.add_argument('--' + name,
                default=default,
                required=not default,
            )

    def add_arguments(self):
        pass

    def make_oath_session(self, args=None):
        args = args or self.args
        from .oath import OathSession
        return OathSession(
            client_key=args.client_key,
            client_secret=args.client_secret,
            resource_owner_key=args.owner_key,
            resource_owner_secret=args.owner_secret,
        )

    def run(self, argv=None):

        self.args = self.parser.parse_args(argv)

        self.db = Database(self.args.username + '.sqlite')
        self.db.create(if_not_exists=True)

        self.oath = self.make_oath_session(self.args)

        return self.main(self.args)

    def main(self, args):
        raise NotImplementedError()


