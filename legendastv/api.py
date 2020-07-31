# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Legendas.TV website API
"""

import logging
import os
import re
import typing as t
import urllib.parse

from   datetime import datetime

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

    def _get(self,
        url:      str,
        postdata: dict = None,
        timeout:  int  = 0,
        stream:   bool = False,
    ) -> requests.Response:
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
            response = self._session.request(method, url, headers=headers,
                                             stream=stream, **kwargs)
            response.raise_for_status()
        except requests.HTTPError as e:
            raise HttpEngineError(e, errno=e.response.status_code)
        except requests.Timeout as e:
            raise TimeoutError(e)  # stdlib
        except requests.ConnectionError as e:
            raise ConnectionError(e)  # stdlib

        return response

    def download(self, url:str, savedir:str, filename="", overwrite:bool=True) -> str:
        # Handle dir
        savedir = os.path.expanduser(savedir)
        os.makedirs(savedir, exist_ok=True)

        try:
            with self._get(url, stream=True) as response:
                response.raise_for_status()

                # If save name is not set, use the downloaded file name
                if not filename:
                    filename = response.url.rstrip("/")
                # Get the full path
                filename = os.path.join(savedir, os.path.basename(filename))

                if not overwrite and os.path.isfile(filename):
                    log.debug("using cached file: %s", filename)
                    return filename

                log.debug("downloading to: %s", filename)
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=None):
                        if chunk:
                            f.write(chunk)

        except requests.HTTPError as e:
            raise HttpEngineError(e, errno=e.response.status_code)
        except requests.Timeout as e:
            raise TimeoutError(e)  # stdlib
        except requests.ConnectionError as e:
            raise ConnectionError(e)  # stdlib

        return filename

    def get(self, url:str, *a, **kw) -> str:
        """Return content from an URL"""
        return self._get(url, *a, **kw).text

    def json(self, url:str, *a, **kw):
        """Load JSON content from an URL"""
        return self._get(url, *a, **kw).json()

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

    _title_mapping = dict(
        id       = 'id_filme',
        category = 'tipo',  # used to determine subclass
        title    = 'dsc_nome',
        native   = 'dsc_nome_br',
        thumb    = 'dsc_imagen',
        year     = 'dsc_data_lancamento',
        season   = 'temporada',  # only for Season subclass
        imdb_id  = 'id_imdb',
        synopsis = 'dsc_sinopse',
        user_id  = 'id_usuario',
        # Unused fields and example values:
        # "int_genero":         "1021",
        # "dsc_sinopse":        "...",
        # "dsc_url_imdb":       "http://www.imdb.com/title/tt0082186/",
        # Not derived from 'id_imdb', not standartized. Real examples:
        # [36413] "http://www.imdb.com/title/tt2338096/" - Most common
        # [41202] "http://www.imdb.com/title/tt2314952"  - No trailing slash
        # [81698] "http://uk.imdb.com/title/tt0081698"   - Alt subdomain
        # [22597] "www.imdb.com/title/tt1216475/"        - Missing scheme
        # "soundex":            "KLXF0TTNS",
        # "flg_liberado":       "1",
        # "dsc_data_liberacao": None,
        # "dsc_data":           None,
        # "dsc_metaphone_us":   "KLXF0TTNS",
        # "dsc_metaphone_br":   "FRTTTS",
        # "episodios":          None,
        # "flg_seriado":        None,
        # "last_used":          "1373185369",
        # "deleted":            False,
    )

    _re_subtitle = re.compile(
        r'<div class="(?P<subtype>[^" ]*)">.+?/download/(?P<hash>[a-f0-9]+)/'
        r'(?P<title>[^/]*?)/[^>]*>(?P<release>[^<]*)<.*?(?P<downloads>\d*) '
        r'downloads, nota (?P<rating>[^,]*),[^>]*>(?P<username>[^<]*)</a> em '
        r'(?P<date>[^<]*)<.*?/idioma/\w+_(?P<language>\w+)[^>]+></div>'
    )
    _re_nextpage = '<a href="([^"]*)" class="load_more">'

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

    def search_titles(self, query:str) -> t.List[model.Title]:
        """Main API method to search titles from a query text"""
        url = "/legenda/sugestao/" + self.quote_partial(query)
        try:
            json: t.List[dict] = self.json(url)
        except HttpEngineError as e:
            log.error(e)
            return []

        titles: t.List[model.Title] = []
        for data in json:
            try:
                title = self._title_from_json(data)
            except u.LegendasTVError as e:
                log.error(e)
                continue
            log.debug(repr(title))
            titles.append(title)
        return titles

    def _title_from_json(self, data:dict) -> model.TTitle:
        # Map raw JSON data to class attributes
        try:
            kwargs = {k: data['_source'].get(v) for k, v in self._title_mapping.items()}
        except KeyError as e:
            raise u.LegendasTVError("Missing expected key %r: %s", e.message, data)

        # Type casting and data formatting
        for k in ('id', 'year', 'season', 'imdb_id', 'user_id'):
            kwargs[k] = u.toint(kwargs[k])
        try:
            category = model.Category(kwargs.pop('category'))
        except ValueError as e:
            # 'X' is not a valid Category
            raise u.LegendasTVError("%s: %s", e.args[0], data)

        # Integrity checks
        if category == model.Category.MOVIE and kwargs['season']:
            log.warning("Movie with season (%r): %s", kwargs['season'], data)
        if category == model.Category.SEASON and not kwargs['season']:
            log.warning("Season with invalid season (%r): %s", kwargs['season'], data)
        if not (kwargs['title'] and kwargs['native']):
            log.warning("Empty original or native title: %s", data)

        # Inject source provider and data, for future use
        kwargs['_ltv'] = self
        kwargs['_raw'] = data

        return model.Title.from_category(category, kwargs)

    def search_subtitles(self,
        title_id: int  = 0,
        lang:     str  = "",
        query:    str  = "",
        subtype:  str  = "",
    ) -> t.List[model.Subtitle]:
        """Return subtitles from a given title ID or query"""
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
        subtype  = str(subtype) or allchar
        page     = 0

        url = f"/legenda/busca/{query}/{lang}/{subtype}/{page}/{title_id}/"

        subs: t.List[model.Subtitle] = []
        while url:
            page += 1
            try:
                html = self.get(url)
            except (HttpEngineError, ConnectionError, TimeoutError) as e:
                log.error(e)
                return subs

            for data in re.finditer(self._re_subtitle, html):
                s = data.groupdict()
                sub = model.Subtitle(
                    # Independent attributes
                    _ltv        = self,
                    _raw        = data.group(0),
                    hash        = s['hash'],
                    url         = self.download_url + s['hash'],
                    title       = s['title'],
                    downloads   = u.toint(s['downloads']),
                    rating      = u.toint(s['rating'], None),
                    date        = datetime.strptime(s['date'].strip(), '%d/%m/%Y - %H:%M'),
                    username    = s['username'],
                    release     = s['release'],
                    subtype     = model.SubType(s['subtype'][:1]),
                    language    = self.langflags.get(s['language'], None)
                )
                #if u.options['cache']: self.cache(sub.flag)
                log.debug(repr(sub))
                subs.append(sub)

            # Page control
            nextpage = re.search(self._re_nextpage, html)
            if nextpage:
                url = nextpage.group(1)
            else:
                url = ""

        return subs

    def download_subtitle(self,
        filehash:  str,
        savedir:   str,
        basename:  str  = "",
        overwrite: bool = True
    ) -> str:
        """Download a subtitle given its ID (hash), and return its saved path.

        Save the archive as dir/basename, using the basename provided or,
        if empty, the one returned from the website.
        """
        if not self.auth:
            log.warning("Subtitle download requires authentication.")

        url = '/downloadarquivo/' + filehash

        try:
            path = self.download(url, savedir, basename, overwrite=overwrite)
        except (HttpEngineError, ConnectionRefusedError, TimeoutError) as e:
            log.error(e)
            return

        return path
