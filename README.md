Legendas.TV API
===============

Library and command-line tools to search, download and extract subtitles from Legendas.TV website,
world's largest repository of Brazilian Portuguese Movie/TV Series subtitles.


Usage
-----

#### Library

``` pycon
>>> import legendastv
>>> ltv = legendastv.LegendasTV()  # Authentication not needed for searches
>>> titles = ltv.search_title('dragon')
>>> for title in titles:
...     print(repr(title))
...
<Cartoon(id=47064, season=8, year=2018, title='Dragons: Race to the Edge ', imdb_id=4816058)>
<Cartoon(id=45294, season=7, year=2017, title='Dragons: Race To The Edge', imdb_id=4816058)>
<Cartoon(id=43604, season=6, year=2017, title='Dragons: Race To The Edge', imdb_id=4816058)>
<Cartoon(id=43615, season=6, year=2017, title='Dragons: Race To The Edge', imdb_id=4816058)>
<Cartoon(id=41277, season=5, year=2016, title='Dragons: Race To The Edge', imdb_id=4816058)>
<Season(id=34582, season=4, year=2014, title='Dragon Ball Kai', imdb_id=0)>
<Season(id=38301, season=3, year=2015, title='Dragons: Race to the Edge', imdb_id=2325846)>
<Cartoon(id=30691, season=2, year=2013, title='Dragons: Riders of Berk', imdb_id=2325846)>
<Cartoon(id=53503, season=1, year=2020, title='Deathstroke: Knights & Dragons', imdb_id=10394706)>
<Cartoon(id=48774, season=1, year=2018, title='The Dragon Prince', imdb_id=8688814)>
<Cartoon(id=38352, season=1, year=2015, title='Dragon Ball Super', imdb_id=4644488)>
<Cartoon(id=39612, season=1, year=2015, title="Chaos Dragon: Sekiryuu Sen'eki", imdb_id=4537640)>
<Season(id=46758, season=1, year=2018, title='Attenborough and the Sea Dragon', imdb_id=7764186)>
<Movie(id=31458, year=1990, title='Dragon Pearl', imdb_id=0)>
<Movie(id=24624, year=2004, title='Dragon Storm', imdb_id=377808)>
<Movie(id=39356, year=2014, title='The Christmas Dragon', imdb_id=3918686)>
<Movie(id=8757, year=2004, title='Dragons Alive', imdb_id=954398)>
<Movie(id=11638, year=2007, title='Iryu Team Medical Dragon 2nd J-Drama', imdb_id=0)>
<Movie(id=23943, year=2011, title='Age of the Dragons', imdb_id=1594917)>
<Movie(id=31326, year=2013, title='The Crown and the Dragon', imdb_id=1913178)>
<Movie(id=47020, year=1993, title='Doragon Booru Zetto: Ginga Giri-Giri!! Butchigiri no Sugoi Yatsu', imdb_id=0)>
<Movie(id=50275, year=1967, title='Dragon Inn', imdb_id=60635)>
<Movie(id=49920, year=1979, title='Long quan', imdb_id=79484)>
<Movie(id=11049, year=1991, title='Xin qi long zhu', imdb_id=122050)>
<Movie(id=13242, year=2009, title='Dragonball: Evolution', imdb_id=1098327)>
<Movie(id=19966, year=2000, title='Dragonheart: A New Beginning', imdb_id=214641)>
<Movie(id=20191, year=2010, title='How to Train Your Dragon', imdb_id=892769)>
<Movie(id=20273, year=2009, title='The Girl with the Dragon Tattoo', imdb_id=1132620)>
<Movie(id=20999, year=1988, title="Dragon Ball: Goku's Fire Fighting Regiment", imdb_id=1297444)>
<Movie(id=22128, year=1989, title='Dragon Ball Z: Son Goku Super Star', imdb_id=142235)>
>>>
>>> title = [t for t in titles if t.imdb_id == 2325846 and t.season == 2][0]
>>> print(title)
Dragons: Riders of Berk S02 [Dragões: Defensores de Berk - 2a Temporada] - 2013
>>> title.imdb_url
'https://www.imdb.com/title/tt2325846/'
>>> title.synopsis[:75]
'O garoto viking Soluço, seu dragão Banguela, e demais amigos estão de volta'
>>>
>>> subs = ltv.search_subtitles(title.id)
>>> for sub in subs[:20]:
...     print(sub)
...
<http://legendas.tv/downloadarquivo/531da7dbcc0d1> * Dragons.Defenders.of.Berk.S02E20.Cast.Out.Part.2.WEB-DL.x264.AAC-MP3-iTOONZ
<http://legendas.tv/downloadarquivo/5318e3e02306e> * Dragons.Defenders.of.Berk.S02E19.WEB-DL.x264.AAC-MP3-iTOONZ
<http://legendas.tv/downloadarquivo/5315ec83768be> * Dragons.Defenders.of.Berk.S02E18.WEB-DL.x264.AAC-MP3-2kim-iTOONZ
<http://legendas.tv/downloadarquivo/530bb338bf91b>   Dragons.Defenders.of.Berk.S02E18.Bing.Bang.Boom.720p.WEB-DL.DD5.1.AAC2.0.H.264-iT00N
<http://legendas.tv/downloadarquivo/53094e342b022> * Dragons.Defenders.of.Berk.S02E17.720p.WEB-DL.x264.AAC-iT00NZ
<http://legendas.tv/downloadarquivo/53052a62b65a9> * Dragons.Defenders.of.Berk.S02E16.720p.WEB-DL.DD5.1.AAC2.0.H.264-iT00NZ-1080p-2kimik2
<http://legendas.tv/downloadarquivo/5304ec681278c> * Dragons.Defenders.of.Berk.S02E15.720p.WEB-DL.DD5.1.AAC2.0.H.264-iT00NZ-1080p-2kimik2.m
<http://legendas.tv/downloadarquivo/52facd49f1af5>   Dragons.Defenders.of.Berk.S02E15.A.Tale.of.Two.Dragons.WEB-DL.x264.AAC
<http://legendas.tv/downloadarquivo/52e908715ec41> * Dragons.Defenders.of.Berk.S02E14.WEB-DL.XviD-AAC-iTOONZ
<http://legendas.tv/downloadarquivo/52e1c2a839320> * Dragons.Defenders.of.Berk.S02E13.720p.WEB-DL/1080p
<http://legendas.tv/downloadarquivo/52ddc2b54c8f9> * Dragons.Defenders.of.Berk.S02E12.WEB-DL.XviD-AAC-iTOONZ
<http://legendas.tv/downloadarquivo/52dac9369d516>   Dragons.Defenders.of.Berk.S02E12.The.Flight.Stuff.720p.Tom-Bom
<http://legendas.tv/downloadarquivo/52af7a007250b> * Dragons.Defenders.of.Berk.S02E11.WEB-DL.XviD-AAC-iTOONZ
<http://legendas.tv/downloadarquivo/52adf6f524915> * Dragons.Defenders.of.Berk.S02E10.WEB-DL.XviD-AAC-iTOONZ
<http://legendas.tv/downloadarquivo/52ab717098895>   Dragons.Defenders.of.Berk.S02E11.A.View.to.a.Skrill.Part.2.720p.WEB-DL.x264.AAC
<http://legendas.tv/downloadarquivo/529b7946cd9bc> * Dragons.Defenders.of.Berk.S02E09.WEB-DL.XviD-AAC-iTOONZ
<http://legendas.tv/downloadarquivo/5293f7c1e33c7> * Dragons.Defenders.of.Berk.S02E08.WEB-DL.XviD-AAC-iTOONZ
<http://legendas.tv/downloadarquivo/528c1a8cc3ea1> * Dragons.Defenders.of.Berk.S02E07.WEB-DL.XviD-AAC-iTOONZ
<http://legendas.tv/downloadarquivo/528bb3c260e94>   Dragons.Defenders.of.Berk.S02E07.Worst.in.Show.720p.WEB-DL.DD5.1.AAC2.0.H.264-iT00NZ
<http://legendas.tv/downloadarquivo/528a857907554>   Dragons.Defenders.of.Berk.S02E08.Appetite.for.Destruction.720p.WEB-DL.x264.AAC
>>>
>>> import guessit  # Truly recommended! Soon incorporated
>>> for sub in subs:
...     guess = guessit.guessit(sub.release)
...     if guess['episode'] == 7 and sub.featured:
...             break
...
>>> import pprint  # Great for debugging!
>>> pprint.pprint(vars(sub))
{'date': datetime.datetime(2013, 11, 20, 0, 12),
 'downloads': 1576,
 'featured': True,
 'flag': 'http://i.legendas.tv/idioma/icon_brazil.png',
 'hash': '528c1a8cc3ea1',
 'language': None,
 'pack': False,
 'rating': 10,
 'release': 'Dragons.Defenders.of.Berk.S02E07.WEB-DL.XviD-AAC-iTOONZ',
 'title': 'Dragons_Riders_of_Berk',
 'url': 'http://legendas.tv/downloadarquivo/528c1a8cc3ea1',
 'username': 'LegendasEmSerie'}
>>>
```
Looks like we have a winner!

#### Command-line (soon!)

```sh
$ legendastv --help
```


Installing
----------

#### From Git:

```sh
git clone https://github.com/MestreLion/ltv
cd ltv
pip install --user -e .
```

#### From PyPi (soon!):

```sh
pip install --user <package>
```


Contributing
------------

Patches are welcome! Fork, hack, request pull!

If you find a bug or have any enhancement request, please open a [new issue](https://github.com/MestreLion/git-tools/issues/new)


Author
------

Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>

License and Copyright
---------------------
```
Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
```
