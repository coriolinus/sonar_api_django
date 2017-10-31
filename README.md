# sonar

_We're not just ships passing in the night; we're submarines lost in the depths, wholly invisible to each other until we actively ping._

`sonar` is a basic Twitter clone, intended to run on a free-tier AWS stack as a demonstration project for my portfolio. Still, maybe it could take off and turn me into an internet billionaire, right?

## Intended features

These features need to be implemented in order for me to consider this a complete demo project.

- [X] user signup / authentication
- [X] user profiles (handle, real name, brief bio)
- [ ] user can create a `ping`: short message up to 140 chars
- [ ] user view showing most recent pings
- [ ] follow another user
- [ ] timeline view showing your pings and those of those people you follow
- [ ] timeline will only ever be linear
- [ ] http addresses auto-expand into links
- [ ] individual ping permalink view
- [ ] individual ping replies view
- [ ] user tags link to user view
- [ ] mentions view showing people writing about you
- [ ] block another user (they cannot see you; you cannot see them)
- [ ] user notifications on tagging
- [ ] hashtags / hashtag search view

## Horizon features

These features would be great, but probably won't happen unless this starts to get a real userbase.

- [ ] users can 'like' pings
- [ ] liked pings view
- [ ] users can 'echo' (retweet) pings. probably just links to it; we don't want the one-button retweet culture from twitter.
- [ ] password reset via email feature
- [ ] email notifications on mentions
- [ ] general search
- [ ] report a ping/user (don't want to take twitter's cavalier attitude against the trolls)
- [ ] inline photos / video
- [ ] log in with twitter to import your contacts
- [ ] twitter bot using sentiment analysis and search to find tweets criticizing twitter, ideally for non-linear-timeline or terrible troll issues, and suggesting sonar as a replacement.

## Architecture

This project is the backend to the sonar website, implementing all features via a REST API. It's built in Python3 via Django and the Django Rest Framework.

I'll build a frontend later, probably as a separate project.
