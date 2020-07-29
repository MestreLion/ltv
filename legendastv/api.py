# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Legendas.TV website API
"""

import logging
import re
import typing as t
import urllib.parse

from   datetime import datetime

import lxml.html
import requests

from . import util as u
from . import model


log = logging.getLogger(__name__)


class HttpEngineError(u.LegendasTVError, IOError):
    """Base class for HTTP and connection related exceptions"""


class HttpEngine:
    """Base class to handle HTTP requests.

    Implements basic HTTP operations like GET'ing pages, POST'ing data, download
    files and cache content in a transparent, library-agnostic way

    Allow LegendasTV class below to be fully agnostic.
    Currently uses python-requests as backend, and wraps a few urllib.parse utilities
    """

    def __init__(self, base_url:str="", *, default_scheme:str="http", timeout:int=30):
        """Set the normalized base_name and initialize a session object.

        A session object will transparently handle cookies in all subsequent requests.
        """
        self._session = requests.Session()
        self.timeout = timeout

        # Normalize base_url, prepending default scheme if missing
        scheme, netloc, path, q, f  = urllib.parse.urlsplit(base_url, default_scheme)
        if not netloc:
            netloc, _x, path = path.partition('/')
        self.base_url = urllib.parse.urlunsplit((scheme, netloc, path, q, f))

    def _get(self, url:str, postdata:dict=None, timeout:int=0) -> requests.Response:
        """Send an HTTP request, either GET or POST, keeping session and cookies.

        <postdata> is a dict with name/value pairs. If falsy, URL is retrieved
        using GET method, otherwise POST the data.

        <url> can be absolute or relative to self.base_url

        <timeout> in seconds. Zero to use the default timeout, negative for no timeout.
        """
        url = self.absurl(url)
        headers = {
            'User-Agent': 'LTV/0.1',  # It seems legendas.tv is blocking python-requests
        }
        kwargs: dict = {}

        if not timeout:
            timeout = self.timeout
        if timeout > 0:
            kwargs['timeout'] = timeout

        if postdata:
            method = 'POST'
            kwargs['data'] = postdata
            log.debug("%s %s %s", method, url, postdata)
        else:
            method = 'GET'
            log.debug("%s %s",    method, url)

        try:
            response = self._session.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
        except requests.HTTPError as e:
            raise HttpEngineError(e, errno=e.response.status_code)
        except requests.Timeout as e:
            raise TimeoutError(e)  # stdlib
        except requests.ConnectionError as e:
            raise ConnectionError(e)  # stdlib

        return response

    def get(self, url:str, *a, **kw) -> str:
        """Return content from an URL"""
        return self._get(url, *a, **kw).text

    def json(self, url:str, *a, **kw):
        """Load JSON content from an URL"""
        return self._get(url, *a, **kw).json()

    def parse(self, url:str, *a, **kw) -> lxml.etree.ElementTree:
        """Parse HTML content from an URL and return an ElementTree object"""
        return lxml.html.fromstring(self.get(url, *a, **kw))

    def absurl(self, url_path:str) -> str:
        """Join the Base URL with an URL path to get an absolute, full URL"""
        return urllib.parse.urljoin(self.base_url, url_path)

    def quote_partial(self, part:str) -> str:
        """URL-Encode a partial URL, including '/', using urllib.parse.quote_plus()"""
        return urllib.parse.quote_plus(part).replace(":", " ").strip()


class LegendasTV(HttpEngine):
    """Main class for accessing Legendas.TV website"""
    # TODO: Composite HttpEngine instead of subclassing it
    url = "http://legendas.tv/"
    thumbs_url = "http://i.legendas.tv/poster/214x317/"
    download_url = url + 'downloadarquivo/'

    languages = dict(
        pb = dict(id= 1, flag="brazil",  name="Português-BR"),
        en = dict(id= 2, flag="usa",     name="Inglês"),
        es = dict(id= 3, flag="es",      name="Espanhol"),
        fr = dict(id= 4, flag="fr",      name="Francês"),
        de = dict(id= 5, flag="de",      name="Alemão"),
        ja = dict(id= 6, flag="japao",   name="Japonês"),
        da = dict(id= 7, flag="denmark", name="Dinamarquês"),
        no = dict(id= 8, flag="norway",  name="Norueguês"),
        sv = dict(id= 9, flag="sweden",  name="Sueco"),
        pt = dict(id=10, flag="pt",      name="Português-PT"),
        ar = dict(id=11, flag="arabian", name="Árabe"),
        cs = dict(id=12, flag="czech",   name="Checo"),
        zh = dict(id=13, flag="china",   name="Chinês"),
        ko = dict(id=14, flag="korean",  name="Coreano"),
        bg = dict(id=15, flag="be",      name="Búlgaro"),
        it = dict(id=16, flag="it",      name="Italiano"),
        pl = dict(id=17, flag="poland",  name="Polonês"),
    )
    langflags = {v['flag']: k for k, v in languages.items()}

    _re_lang = re.compile(r"idioma/\w+_(\w+)\.")

    def __init__(self, username:str="", password:str="", **kwargs):
        super().__init__(kwargs.pop('base_url', "") or self.url, **kwargs)
        self.auth = self.login(username, password)

    def login(self, username:str, password:str) -> bool:
        if not (username and password):
            return False

        url = self.absurl('/login')
        log.info("Logging in %s as %s", url, username)

        try:
            content = self.get(url, {
                '_method':              'POST',
                'data[User][username]': username,
                'data[User][password]': password,
                'data[lembrar]':        'on',
            })
        except (HttpEngineError, ConnectionRefusedError, TimeoutError) as e:
            errno = getattr(e, 'errno', 0)  # from HttpEngineError
            if errno and errno not in (513,):  # Service Unavailable
                raise
            log.error(e)
            raise u.LegendasTVError(f"Legendas.TV website is down! [{e}]")

        # Check successful login: logout link available
        self.auth = 'href="/users/logout"' in content
        return self.auth

    def search_title(self, text:str) -> t.List[model.Title]:
        url = "/legenda/sugestao/" + self.quote_partial(text)
        try:
            data: t.List[dict] = self.json(url)
        except HttpEngineError as e:
            log.error(e)
            data = []

        titles: t.List[model.Title] = []
        for title in data:
            try:
                title = model.Title.from_data(title)
            except u.LegendasTVError as e:
                log.error(e)
                continue
            log.debug(repr(title))
            titles.append(title)
        return titles

    def search_subtitles(self,
        title_id: int  = 0,
        lang:     str  = "",
        query:    str  = "",
        subtype:  str  = "",
    ) -> t.List[model.Subtitle]:
        """Return subtitles from a given title query or ID"""
        allchar = '-'
        subtypes = [__.value for __ in model.SubType]

        if not (title_id or query):
            raise u.LegendasTVError("Subtitle search require either title ID or a query text")
        if lang and lang not in self.languages:
            raise u.LegendasTVError("Invalid language for subtitle search: %s", lang)
        if subtype and subtype not in subtypes:
            raise u.LegendasTVError("Invalid subtitle type: %s (accepts: %s)", subtype, subtypes)

        title_id = title_id or allchar
        lang     = self.languages.get(lang, {}).get('id', allchar)
        query    = self.quote_partial(query or allchar)
        subtype  = subtype or allchar
        page     = 0

        url = f"/legenda/busca/{query}/{lang}/{subtype}/{page}/{title_id}/"

        subs: t.List[model.Subtitle] = []
        while url:
            page += 1
            try:
                tree = self.parse(url)
            except (HttpEngineError, ConnectionError, TimeoutError) as e:
                log.error(e)
                return subs

            for el in tree.xpath(".//article/div"):
                if el.attrib['class'].startswith('banner'): continue
                data = el.xpath(".//text()")
                dataurl = el.xpath(".//a")[0].attrib['href'].split('/')
                dataline = data[2].split(' ')
                flag = el.xpath("./img")[0].attrib['src']
                sub = model.Subtitle(
                    # Independent attributes
                    raw         = lxml.html.tostring(el, encoding='unicode'),
                    hash        = dataurl[2],
                    title       = dataurl[3],
                    downloads   = u.toint(dataline[0]),
                    rating      = u.toint(dataline[3][:-1], None),
                    date        = datetime.strptime(data[4].strip()[3:], '%d/%m/%Y - %H:%M'),
                    username    = data[3],
                    release     = data[1],
                    pack        = el.attrib['class'] == 'pack',
                    featured    = el.attrib['class'] == 'destaque',
                    language    = self.langflags.get(re.search(self._re_lang, flag).group(1))
                )
                # Derived attributes
                sub.url = self.download_url + sub.hash
                if sub.pack and sub.release.startswith("(p)"):
                    sub.release = sub.release[3:]

                #if u.options['cache']: self.cache(sub.flag)
                log.debug(repr(sub))
                subs.append(sub)

            # Page control
            nextpage = tree.xpath("//a[@class='load_more']")
            if nextpage:
                url = nextpage[0].attrib['href']
            else:
                url = ""

        return subs
