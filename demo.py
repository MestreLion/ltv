#!/usr/bin/env python3

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


def wxgui():
    import wx

    class Window(wx.Frame):
        def __init__(self, title):
            super().__init__(None, title=title)
            parent = self  # wx.Panel(self)
            parent.SetBackgroundColour('red')

            panel = wx.Panel(parent)
            panel.SetBackgroundColour('blue')

            grid = wx.GridBagSizer(5, 5)
            grid.Add(wx.TextCtrl(panel, value="hi"), (0, 0), flag=wx.EXPAND)
            grid.AddGrowableCol(0)
            panel.SetSizer(grid)

            outer = wx.BoxSizer()
            outer.Add(panel, 1, flag=wx.GROW | wx.ALL, border=20)
            parent.SetSizerAndFit(outer)

    app = wx.App()
    window = Window('WxWidgets Window Test')
    window.Show()
    app.MainLoop()


def errors():
    import legendastv.api
    http = legendastv.api.HttpEngine(base_name='Website')

    for url in (
        'http://httpbin.org/status/513',  # HTTP Service Unavailable
        'http://localhost:123',           # [Errno 111] Connection refused
        'http://a.a',                     # [Errno -2] Name or service not known
        # 'http://[::1]',                 # [Errno 101] Network is unreachable
        'http://httpbin.org/delay/3',     # Read Timeout
        'http://google.com:81',           # Connect Timeout

    ):
        try:
            http.get(url, timeout=1)
        except Exception as e:
            log.error(repr(e))


def demo():
    import legendastv.filetools as ft
    pprint(ft.extract_archive('data/dummy.rar'))

try:
    log = logging.getLogger(__name__)
    errors()
except LegendasTVError as e:
    log.critical(e)
