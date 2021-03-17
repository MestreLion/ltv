# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Legendas.TV website API
"""

import concurrent.futures
import errno
import datetime
import logging
import os
import re
import socket
import typing as t
import urllib.parse

import requests

# should preferably not import system or config
from . import util as u
from . import model


log = logging.getLogger(__name__)


class HttpEngineError(u.LegendasTVError, IOError):
    """Base class for HTTP and connection related exceptions"""


class HttpEngineHttpError(HttpEngineError):
    """An HTTP error occurred."""


class HttpEngineTimeout(HttpEngineError, TimeoutError):
    """A request timed out when either connecting or reading data."""


class HttpEngineConnectionError(HttpEngineError, ConnectionError):
    """A connection error occurred."""


class HttpEngine:
    """Base class to handle HTTP requests.

    Implements basic HTTP operations like GET'ing pages, POST'ing data, download
    files and cache content in a transparent, library-agnostic way

    Allow LegendasTV class below to be fully agnostic.
    Currently uses python-requests as backend, and wraps a few urllib.parse utilities
    """

    # Simultaneous connections to a single host. Defaults:
    # requests.Session() = 10 (from requests.adapters.DEFAULT_POOLSIZE)
    # concurrent.futures: 5 * os.cpu_count()
    MAX_CONNS = 20  # Enough for all language icons

    _re_errno = re.compile(r'\[[Ee]rrno (?P<errno>[0-9-]+)] (?P<msg>.*)')

    def __init__(self, base_url:str="", base_name:str="", *,
                 default_scheme:str="http", timeout:int=5):
        """Set the normalized base_url and initialize a session object.

        A session object will transparently handle cookies in all subsequent requests.
        """
        self._session = requests.Session()
        self.base_name = base_name
        self.timeout = timeout
        self.base_url = base_url

        # Normalize base_url, prepending default scheme if missing
        scheme, netloc, path, q, f  = urllib.parse.urlsplit(base_url, default_scheme)
        if not netloc:
            # For base_url = 'a.com' or 'a.com/b', urlsplit() puts all in path
            netloc, _x, path = path.partition('/')
        if netloc:
            self.base_url = urllib.parse.urlunsplit((scheme, netloc, path, '', ''))

        # Set ConnectionPool maxsize
        for prefix in list(self._session.adapters):
            adapter = requests.adapters.HTTPAdapter(pool_maxsize=self.MAX_CONNS)
            self._session.mount(prefix, adapter)

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

        <timeout> in seconds. Falsy to use the default timeout, negative for no timeout.
        Note: If both client and server have IPv6, effective timeout time can be doubled,
        See https://github.com/psf/requests/issues/5773
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
        except requests.RequestException as e:
            # Unify message for Timeout, ConnectionError and some HTTP status
            raise self._handle_requests_exception(e, url)

        return response

    def download(self, url:str, savedir:str, filename="", overwrite:bool=True) -> str:

        def fullpath(f):
            return "" if not f else os.path.join(savedir, os.path.basename(f))

        def is_cached(f):
            if f and not overwrite and os.path.isfile(f):
                log.debug("Using cached file: %s", f)
                return True

        savedir = os.path.expanduser(savedir)
        filename = fullpath(filename)

        # Shortcut: if path exists and caching is enabled, don't request server
        if is_cached(filename):
            return filename

        # Handle dir
        os.makedirs(savedir, exist_ok=True)

        try:
            with self._get(url, stream=True) as response:
                response.raise_for_status()

                # If save name is not set, use the downloaded file name
                if not filename:
                    filename = fullpath(response.url.rstrip("/"))

                if is_cached(filename):
                    return filename

                log.debug("Downloading to: %s", filename)
                with open(filename, 'wb') as fd:
                    for chunk in response.iter_content(chunk_size=None):
                        if chunk:
                            fd.write(chunk)

        # response.iter_content() may raise exceptions in addition to self._get()
        except requests.RequestException as e:
            raise self._handle_requests_exception(e, url)

        return filename

    def _handle_requests_exception(self, e:requests.RequestException, url:str) -> IOError:
        """Set message and type for Timeout, ConnectionError and some HTTP status"""
        def err_args(e_, n_=False):
            return (
                '%s is down! [%s]',
                "Network" if n_ else (self.base_name or self.absurl(url)),
                e_
            )

        def delim(e_, d_):
            m_ = str(e_).split(d_[0])[-1].split(d_[1])[0].strip()
            return m_ if len(m_) >= 10 else str(e_)

        if isinstance(e, requests.HTTPError):
            args = err_args(e) if e.response.status_code in (
                503,  # Service Unavailable
            ) else (e,)
            return HttpEngineHttpError(*args, errno=e.response.status_code)

        elif isinstance(e, requests.Timeout):
            msg = delim(e, "()")
            msg = ' '.join((str(errno.ETIMEDOUT), msg.split('=')[0].capitalize()))
            return HttpEngineTimeout(*err_args(msg), errno=errno.ETIMEDOUT)

        elif isinstance(e, requests.ConnectionError):
            # Parse original error message and errno code
            eno, msg = 0, delim(e, ":'")
            m = re.match(self._re_errno, msg)
            if m:
                msg = m.group('msg')
                if m.group('errno'):
                    eno = int(m.group('errno'))
                    msg = ' '.join((str(eno), msg))
            # Tell apart a Server issue from a Client one (or at least try to)
            net = eno in (
                socket.EAI_NONAME,   # -2  Name or service not known (DNS error)
                errno.ENETUNREACH,   # 101 Network is unreachable
            )
            # Some connection errors do not mean Network/Website is down
            args = err_args(msg, net) if eno not in (
                errno.ECONNREFUSED,  # 111 Connection refused
            ) else (msg,)
            return HttpEngineConnectionError(*args, errno=eno)

        return e

    def get(self, url:str, *a, **kw) -> str:
        """Return content from an URL"""
        return self._get(url, *a, **kw).text

    def json(self, url:str, *a, **kw):
        """Load JSON content from an URL"""
        return self._get(url, *a, **kw).json()

    def absurl(self, url_path:str) -> str:
        """Join the Base URL with an URL path to get an absolute, full URL"""
        return urllib.parse.urljoin(self.base_url, url_path)

    @staticmethod
    def quote_partial(part:str) -> str:
        """URL-Encode a partial URL, including '/', using urllib.parse.quote_plus()"""
        return urllib.parse.quote_plus(part).replace(":", " ").strip()


class LegendasTV(HttpEngine):
    """Main class for accessing Legendas.TV website"""
    # TODO: Composite HttpEngine instead of subclassing it
    url = "http://legendas.tv/"
    name = "Legendas.TV"
    _download_url_fmt = url + 'downloadarquivo/{}'
    _thumb_url_fmt    = "http://i.legendas.tv/poster/214x317/{}"
    _langicon_url_fmt = "http://i.legendas.tv/idioma/{}"

    # Intentionally ordered as the website language select box
    _languages = dict(
        pb = dict(id= 1, icon="icon_brazil.png",  name="Português-BR"),
        en = dict(id= 2, icon="icon_usa.png",     name="Inglês"),
        es = dict(id= 3, icon="flag_es.gif",      name="Espanhol"),
        pt = dict(id=10, icon="flag_pt.gif",      name="Português-PT"),
        de = dict(id= 5, icon="flag_de.gif",      name="Alemão"),
        ar = dict(id=11, icon="flag_arabian.gif", name="Árabe"),
        bg = dict(id=15, icon="flag_be.gif",      name="Búlgaro"),
        cs = dict(id=12, icon="flag_czech.gif",   name="Checo"),
        zh = dict(id=13, icon="flag_china.gif",   name="Chinês"),
        ko = dict(id=14, icon="flag_korean.gif",  name="Coreano"),
        da = dict(id= 7, icon="flag_denmark.gif", name="Dinamarquês"),
        fr = dict(id= 4, icon="flag_fr.gif",      name="Francês"),
        it = dict(id=16, icon="flag_it.gif",      name="Italiano"),
        ja = dict(id= 6, icon="flag_japao.gif",   name="Japonês"),
        no = dict(id= 8, icon="flag_norway.gif",  name="Norueguês"),
        pl = dict(id=17, icon="flag_poland.gif",  name="Polonês"),
        sv = dict(id= 9, icon="flag_sweden.gif",  name="Sueco"),
    )
    # Augment languages with derived fields 'code', 'url' and 'path'
    for _ in _languages:
        _languages[_].update(dict(
            code = _,
            path = "",
            url  = _langicon_url_fmt.format(_languages[_]['icon']),
        ))

    _langicons = {v['icon']: k for k, v in _languages.items()}

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
        # Not derived from 'id_imdb', not standardized. Real examples:
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
        r'(?P<date>[^<]*)<.*?/idioma/(?P<langicon>[^\'"]+)[^>]+></div>'
    )
    _re_nextpage = re.compile(r'<a href="([^"]*)" class="load_more">')

    def __init__(self, username:str="", password:str="", **kwargs):
        super().__init__(kwargs.pop('base_url', "") or self.url,
                         '{} website'.format(self.name),
                         **kwargs)
        self.auth = self.login(username, password)
        self.languages = self._languages.copy()

    def get_languages(self, update=False, cachedir:str="") -> dict:
        if update:
            # TODO: Fetch languages from website
            self.languages.update({})

        if not cachedir:
            return self.languages

        # For atomicity, loop and change data on a copy, then update original
        langs = self.languages.copy()

        def fetch(d):
            try:
                p = self.download(d['url'], cachedir, d['icon'], overwrite=False)
            except HttpEngineError as e:
                p = ""
                log.warning("Could not download icon for [%s] %s: %s",
                            d['code'], d['name'], e)
            return d['code'], p

        with concurrent.futures.ThreadPoolExecutor(self.MAX_CONNS) as executor:
            for lang, path in executor.map(fetch, self.languages.values()):
                langs[lang]['path'] = path

        # Update in a single operation and return it
        self.languages = langs
        return self.languages

    def login(self, username:str, password:str) -> bool:
        if not (username and password):
            return False

        url = self.absurl('/login')
        log.info("Logging in %s as %s", url, username)

        content = self.get(url, {
            '_method':              'POST',
            'data[User][username]': username,
            'data[User][password]': password,
            'data[lembrar]':        'on',
        })

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
            raise u.LegendasTVError("Missing expected key %s: %s", e, data)

        # Cast integer fields
        for k in ('id', 'year', 'season', 'imdb_id', 'user_id'):
            kwargs[k] = u.toint(kwargs[k])

        # Cast Category to Enum
        try:
            category = model.Category(kwargs.pop('category'))
        except ValueError as e:
            # 'X' is not a valid Category
            raise u.LegendasTVError("%s: %s", e, data)

        # Add full URLs
        if kwargs.get('thumb'):
            kwargs['thumb'] = self._thumb_url_fmt.format(kwargs['thumb'])

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

        tid      = title_id or allchar
        lang     = self.languages.get(lang, {}).get('id', allchar)
        query    = self.quote_partial(query or allchar)
        subtype  = str(subtype) or allchar
        page     = 0

        url = f"/legenda/busca/{query}/{lang}/{subtype}/{page}/{tid}/"

        subs: t.List[model.Subtitle] = []
        while url:
            page += 1
            try:
                html = self.get(url)
            except HttpEngineError as e:
                log.error(e)
                return subs

            for data in re.finditer(self._re_subtitle, html):
                s = data.groupdict()
                sub = model.Subtitle(
                    # Independent attributes
                    _ltv        = self,
                    _raw        = data.group(0),
                    hash        = s['hash'],
                    url         = self._download_url_fmt.format(s['hash']),
                    title_id    = title_id,
                    title       = s['title'],
                    downloads   = u.toint(s['downloads']),
                    rating      = u.toint(s['rating'], None),
                    username    = s['username'],
                    release     = s['release'],
                    subtype     = model.SubType(s['subtype'][:1]),
                    language    = self._langicons.get(s['langicon'], None),
                    date        = datetime.datetime.strptime(s['date'].strip(),
                                                             '%d/%m/%Y - %H:%M'),
                )
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
        overwrite: bool = False
    ) -> str:
        """Download a subtitle given its ID (hash), and return its saved path.

        Save the archive as dir/basename, using the basename provided or,
        if empty, the one returned from the website.
        """
        if not self.auth:
            raise u.LegendasTVError("Subtitle download requires authentication.")

        url = self._download_url_fmt.format(filehash)

        return self.download(url, savedir, basename, overwrite=overwrite)
