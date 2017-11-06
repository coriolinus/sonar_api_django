# sonar

_We're not just ships passing in the night; we're submarines lost in the depths, wholly invisible to each other until we actively ping._

`sonar` is a basic Twitter clone, intended to run on a free-tier AWS stack as a demonstration project for my portfolio. Still, maybe it could take off and turn me into an internet billionaire, right?

## Minimum Viable Product

- [X] user signup / authentication
- [X] user profiles (handle, real name, brief bio)
- [X] user can create a `ping`: short message up to 140 chars
- [X] individual ping permalink view
- [X] user timeline view showing most recent pings
- [X] timeline will only ever be linear
- [X] follow another user
- [X] unfollow another user
- [X] timeline view showing your pings and those of those people you follow
- [X] reply to a previous ping
- [X] individual ping replies view

## Demo Features

These features need to be implemented in order for me to consider this a complete demo project.

- [X] mentions view showing people writing about/to you
- [X] hashtags / hashtag search view
- [ ] block another user (they cannot see you when logged in; you cannot see them when logged in)

## Horizon features

These features would be great, but probably won't happen unless this starts to get a real userbase.

- [ ] hashtag overview view, sorting them all by popularity / date
- [ ] proper property-based testing (see note below)
- [ ] users can 'like' pings
- [ ] liked pings view
- [ ] users can 'echo' (retweet) pings. probably just links to it; we don't want the one-button retweet culture from twitter.
- [ ] password reset via email feature
- [ ] email notifications on mentions
- [ ] general search
- [ ] report a ping/user (don't want to take twitter's cavalier attitude against the trolls)
- [ ] inline photos / video
- [ ] http addresses auto-expand into links (likely to get pushed to the front end)
- [ ] user tags link to user view (likely to get pushed to the front end)
- [ ] log in with twitter to import your contacts
- [ ] twitter bot using sentiment analysis and search to find tweets criticizing twitter, ideally for non-linear-timeline or terrible troll issues, and suggesting sonar as a replacement.

## Property-based testing

Property-based tests are great, and I've had good results using the [Hypothesis](https://hypothesis.readthedocs.io/en/latest/) library to test REST APIs in the past. However, they take some additional time to implement. However, they do take additional time to implement. I really like them in production code. This, however, is not production code, and it's difficult to justify the additional time that property-based tests require in a demo project.

## Architecture

This project is the backend to the sonar website, implementing all features via a REST API. It's built in Python3 via Django and the Django Rest Framework.

I'll build a frontend later, probably as a separate project.
