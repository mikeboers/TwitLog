import json

from .cli import BaseCommand


class FollowersCommand(BaseCommand):

    def add_arguments(self):
        self.parser.add_argument('-x', '--no-relationships', action='store_true')
        self.parser.add_argument('-X', '--no-profiles', action='store_true')

    def main(self, args):
        if not args.no_relationships:
            self.update_relationships()
        if not args.no_profiles:
            self.update_profiles()

    def update_relationships(self):

        with self.db.connect() as con:

            # Merge the data from the two API sources, and the database.
            users = {}
            for id_ in self.get_follower_ids():
                users.setdefault(id_, {})['is_follower'] = True
            for id_ in self.get_friend_ids():
                users.setdefault(id_, {})['is_friend'] = True
            for row in con.execute('''
                SELECT user.id, rel.is_friend, rel.is_follower
                FROM users as user
                JOIN user_relationships as rel
                ON user.last_relationship_id = rel.id
            '''):
                users.setdefault(row['id'], {})['user'] = row

            for uid, meta in users.iteritems():

                user = meta.get('user')
                is_friend = meta.get('is_friend', False)
                is_follower = meta.get('is_follower', False)

                # Create the user if it is missing.
                if user is None:
                    con.insert('users', {
                        'id': uid
                    })

                # Update relationships.
                if user is None or is_follower != user['is_follower'] or is_friend != user['is_friend']:
                    new_rel_id = con.insert('user_relationships', {
                        'user_id': uid,
                        'is_follower': is_follower,
                        'is_friend': is_friend,
                    })
                    con.update('users', {
                        'last_relationship_id': new_rel_id
                    }, where={'id': uid})

    def get_follower_ids(self):
        ids = []
        for chunk in self.oath.iter_json('followers/ids', params=dict(screen_name=self.args.username)):
            ids.extend(chunk['ids'])
        return ids

    def get_friend_ids(self):
        ids = []
        for chunk in self.oath.iter_json('friends/ids', params=dict(screen_name=self.args.username)):
            ids.extend(chunk['ids'])
        return ids

    def update_profiles(self):
        all_ids = []
        with self.db.connect() as con:
            for row in con.execute('''
                SELECT user.id
                FROM users as user
                WHERE user.last_profile_id IS NULL
            '''):
                all_ids.append(row['id'])
        for i in xrange(0, len(all_ids), 100):
            ids_str = ','.join(map(str, all_ids[i:i + 100]))
            profiles = self.oath.get_json('users/lookup', params={
                'user_id': ids_str,
            })
            for profile in profiles:
                profile.pop('status', None) # We don't care about it.
                pid = con.insert('user_profiles', {
                    'user_id': profile['id'],
                    'json': json.dumps(profile, sort_keys=True),
                })
                con.update('users', {'last_profile_id': pid}, {'id': profile['id']})

