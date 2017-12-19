# RSSFeeder

> RSSFeeder requires an AWS IAM user that can create a dynamodb table. It can be configured via `.credentials` file

RSSFeeder has two classes

- Feeder : reads feeds from the source and keeps track of seen feeds in database
- Poster : this is the abstract class that you will implement

Feeder class reads the RSS feeds from the provided feed url. A
sample implementation is below. Since RSSFeeder will keep track the feeds
already seen, you won't need to manage duplicates.

```
import requests
from feeder import Feeder, Poster

class MyPoster(Poster):
    def __init__(self, webhook):
        self.webhook = webhook

    def post(self, feed):
        # your code to post the feed to another service
        # defined by `self.webhook`
        print('Posting the feed to Webhook: {}'.format(self.webhook))

        content += feed.title + '\n'
        content += feed.published + '\n'
        content += feed.summary + '\n'
        content += feed.link + '\n'

        req = requests.post(self.webhook, data=content)

feed_url = 'http://feeds.feedburner.com/amazon/newsblog'
dynamodb_table = 'rssfeedlogs'
poster = MyPoster('https://aRestInterface.com/post')

feeder = Feeder(feed_url, dynamodb_table, poster)
feeder.process_feeds()

```