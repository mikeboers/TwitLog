from setuptools import setup, find_packages

setup(
    name='twitlog',
    packages=find_packages('.'),
    entry_points={
        'console_scripts': '''
            twitlog-analytics = twitlog.analytics:AnalyticsCommand.make_and_run
            twitlog-followers = twitlog.followers:FollowersCommand.make_and_run
        ''',
    },
)
