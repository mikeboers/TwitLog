
_migrations = []
patch = _migrations.append


@patch
def create_config_table(con):
    con.execute('''CREATE TABLE config (
        key TEXT UNIQUE NOT NULL,
        value TEXT NOT NULL
    )''')


@patch
def create_user_tables(con):
    con.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY NOT NULL,
        name TEXT,
        last_profile_id INTEGER REFERENCES user_profiles (id),
        last_relationship_id INTEGER REFERENCES user_relationships (id)
    )''')
    con.execute('''CREATE TABLE user_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT (datetime('now')),
        user_id INTEGER NOT NULL REFERENCES users (id),
        json TEXT NOT NULL
    )''')
    con.execute('''CREATE TABLE user_relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT (datetime('now')),
        user_id INTEGER NOT NULL REFERENCES users (id),
        is_friend BOOLEAN NOT NULL,
        is_follower BOOLEAN NOT NULL
    )''')


@patch
def create_tweet_tables(con):
    con.execute('''CREATE TABLE tweets (
        id INTEGER PRIMARY KEY NOT NULL,
        json TEXT,
        last_analytics_id INTEGER REFERENCES tweet_analytics(id)
    )''')
    con.execute('''CREATE TABLE tweet_analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT (datetime('now')),
        tweet_id INTEGER NOT NULL REFERENCES tweets (id),
        json TEXT NOT NULL
    )''')
