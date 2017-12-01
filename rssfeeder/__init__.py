"""
Keeps state of RSS feeds and posts new feeds
Used an AWS DynamoDB table to track previously
seen feeds.

Feeder class needs a Poster class which implements
post method. post method is responsible from
posting the feed to desired destination

Table structure
--------
- rssurl : url for the RSS feed
- feedid : Unique ID per feed
- published : Published date for the feed
- title : Title of the feed
- link: URL for the feed
"""

from abc import ABCMeta, abstractmethod
import feedparser
import boto3
from botocore.exceptions import ClientError

class Poster():
    """
    Implements the class that posts the feed
    retrieved by Feeder
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def post(self, feed):
        """ Post the feed to destination """
        raise NotImplementedError


class Feeder():
    """ RSS to Chime """
    def __init__(self, feed_url, table, poster):
        self._feed_url = feed_url
        self._table_name = table
        self._poster = poster
        self._dynamodb = boto3.resource('dynamodb')
        self._table = self._dynamodb.Table(table)
        print('\nChecking feeds at {}'.format(feed_url))
        self._modified = self.get_modified()

    def get_modified(self):
        """ Get last modified date for the feed """
        while True:
            try:
                response = self._table.get_item(
                    Key={
                        'rssurl': self._feed_url,
                        'feedid': '0'
                    }
                )
                if 'Item' in response:
                    item = response['Item']
                    return item['published']
            except ClientError as err:
                if err.response['Error']['Code'] == 'ResourceNotFoundException':
                    print('DynamoDB table {} is not available, creating.'.format(self._table_name))
                    self.create_table()
                    continue
                else:
                    raise err
            break
        return None

    def create_table(self):
        """ Creates dynamodb table if it doesn't exist """
        # Create the DynamoDB table.
        try:
            table = self._dynamodb.create_table(
                TableName=self._table_name,
                KeySchema=[
                    {
                        'AttributeName': 'rssurl',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'feedid',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'rssurl',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'feedid',
                        'AttributeType': 'S'
                    },
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
        except ClientError as err:
            if err.response['Error']['Code'] == 'ResourceInUseException':
                print('Table {} already exists.'.format(self._table_name))
        else:
            table.meta.client.get_waiter('table_exists').wait(TableName=self._table_name)
            print('Table {} is ready.'.format(self._table_name))

    def process_feeds(self):
        """ Gets feeds from the source """
        if self._modified is None:
            feeds = feedparser.parse(self._feed_url)
        else:
            print('modified {}'.format(self._modified))
            feeds = feedparser.parse(self._feed_url, modified=self._modified)
        if feeds.status == 200:
            print('There are {} feeds in the feed.'.format(len(feeds['entries'])))
            sorted_feeds = feeds['entries']
            sorted_feeds.sort(key=lambda item: item['published'])
            for feed in sorted_feeds:
                if self.is_duplicate(feed.id) is False:
                    self.post(feed)
                else:
                    print('Feed {} is seen before'.format(feed.id))
            self.update_modified(feeds.modified)
        elif feeds.status == 304:
            print('No new feeds at {}'.format(self._feed_url))
        else:
            raise Exception('Can not read the feeds')

    def is_duplicate(self, feedid):
        """ Check if feed was seen before """
        response = self._table.get_item(
            Key={
                'rssurl': self._feed_url,
                'feedid': feedid
            }
        )
        if 'Item' in response:
            return True
        return False

    def post(self, feed):
        """ Post the feed to Chime Chat Room """
        if self._poster.post(feed):
            self.record_feed(feed)
        else:
            raise Exception("Could not post the feed")

    def record_feed(self, feed):
        """ record feedid in the database """
        print('recording {} to database'.format(feed.id))
        response = self._table.put_item(
            Item={
                'rssurl': self._feed_url,
                'feedid': feed.id,
                'published': feed.published,
                'title': feed.title,
                'link': feed.link
            }
        )
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise Exception("Can not write to database")

    def update_modified(self, modified):
        """ record modified date in the database """
        print('recording feeds modified date {} to database'.format(modified))
        response = self._table.put_item(
            Item={
                'rssurl': self._feed_url,
                'feedid': '0',
                'published': modified
            }
        )
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise Exception("Can not write to database")