from setuptools import setup

setup(
    name='rssfeeder',
    version='0.1.1',
    description='A library to read RSS feeds and post to different destinations.',
    author='Oz Akan',
    author_email='oz@akan.me',
    url='https://github.com/ozgurakan/rssfeeder',
    keywords=['rss', 'feed', 'aws', 'dynamodb'],
    classifiers=[],
    packages=['rssfeeder'],
    install_requires=['boto3', 'feedparser'],
    python_requires='>=3',
)
