#!/usr/bin/env python3

# Other subtitle websites to consider:
# https://megasubtitles.com/
# https://legendei.to
# https://legendas.dev/


import logging
# Otherwise it's silent
logging.basicConfig(level=logging.DEBUG, format='%(asctime).19s [%(levelname)-5s] %(message)s')
# rebulk, used by guessit, can be incredibly chatty at DEBUG level
logging.getLogger('rebulk').setLevel(logging.WARNING)

from pprint import pprint

from legendastv.util import LegendasTVError

def readme():
    import legendastv as ltv
    api = ltv.LegendasTV()  # Searching titles and subtitles does not require authentication

    titles = api.search_titles("dragon")

    for title in titles:
        print(repr(title))

    title = [t for t in titles if t.imdb_id == 2325846 and t.season == 2][0]
    print(title)
    print(title.imdb_url)
    print(title.synopsis[:75])

    subs = api.search_subtitles(title.id, 'pb')

    for sub in subs[:20]:
        print(sub)

    import guessit  # Truly recommended! Soon incorporated
    for sub in subs:
        guess = guessit.guessit(sub.release)
        if guess['episode'] == 7 and sub.featured:
                break

    pprint(vars(sub))  # Great for debugging!


def extract():
    import legendastv.filetools as ft
    for archive in ('data/legendas_tv_20190624115940875.zip', 'data/legendas_tv_20171115000216000000.rar'):
        pprint(ft.extract_archive(archive, 'data/archives', extlist='srt'))


def demo():
    import legendastv.filetools as ft
    pprint(ft.extract_archive('data/dummy.rar'))

try:
    readme()
except LegendasTVError as e:
    logging.getLogger(__name__).critical(e)
