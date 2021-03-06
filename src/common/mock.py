from datetime import timedelta
from random import choices, randint
from user.models import User

from django.conf import settings
from django.utils.timezone import now

# these are the unique words from jabberwocky
WORDLIST = {
    '--', 'all', 'and', 'arms', 'as', 'awhile', 'back', 'bandersnatch', 'beamish', 'beware',
    'bird', 'bite', 'blade', 'borogoves', 'boy', 'brillig', 'burbled', 'by', 'callay',
    'callooh', 'came', 'catch', 'chortled', 'claws', 'come', 'day', 'dead', 'did', 'eyes',
    'flame', 'foe', 'frabjous', 'frumious', 'galumphing', 'gimble', 'gyre', 'hand', 'has',
    'he', 'head', 'his', 'in', 'it', 'its', 'jabberwock', 'jaws', 'joy', 'jubjub', 'left',
    'long', 'manxome', 'mimsy', 'mome', 'my', 'o', 'of', 'one', 'outgrabe', 'raths', 'rested',
    'shun', 'slain', 'slithy', 'snicker-snack', 'so', 'son', 'sought', 'stood', 'sword',
    'that', 'the', 'thou', 'thought', 'through', 'time', 'to', 'took', 'toves', 'tree',
    'tulgey', 'tumtum', 'twas', 'two', 'uffish', 'vorpal', 'wabe', 'went', 'were',
    'whiffling', 'with', 'wood'
}
try:
    with open('/usr/share/dict/words') as word_file:
        WORDLIST.update((word.strip() for word in word_file.readlines()))
except Exception:
    # we don't care what the problem is; we have a good default
    pass
# remove plurals and possessives and convert to list
WORDLIST = [
    word for word in WORDLIST
    if not (
        ("'" in word) or
        (word.endswith('s') and word[:-1] in WORDLIST) or
        (word.endswith('es') and word[:-2] in WORDLIST) or
        (word.endswith('ies') and word[:-3] + 'y' in WORDLIST)
    )
]


def gen_text(length=settings.PING_LENGTH, hashtags=False, users=False):
    text_words = choices(WORDLIST, k=randint(1, (length // 6)))
    if users:
        usernames = set((u.username for u in User.objects.all()))
        text_words = ['@' + w if w in usernames else w for w in text_words]
    if hashtags:
        text_words = [
            '#' + w if (not w.startswith('@') and randint(0, 9) == 0) else w
            for w in text_words
        ]
    text = ' '.join(text_words)
    if len(text) > length:
        last_space = text.rfind(' ', 0, length)
        if last_space == -1:
            # couldn't find a space, so just truncate
            text = text[:length]
        else:
            text = text[:last_space]
    return text


def gen_times(base=None,
              forwards=True,
              min_interval=timedelta(minutes=1),
              max_interval=timedelta(hours=1)):
    """
    Generator which produces a sequence of times.

    - `base` is the first value which should be returned. If `None`,
        it returns the current time
    - `forwards`: move forward in time if True, backwards if False
    - `min_interval` is a timedelta representing the minimum time before the
        next which should be returned
    - `max_interval` is a timedelta representing the maximum time before the
        next which should be returned

    Note that this has a minimum resolution of 1 second.
    """
    if base is None:
        base = now()
    while True:
        yield base
        td = timedelta(
            seconds=randint(round(min_interval.total_seconds()),
                            round(max_interval.total_seconds()))
        )
        if not forwards:
            td = -td
        base += td
