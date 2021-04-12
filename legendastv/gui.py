# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    GUI classes and functions
"""

import logging

from . import __about__ as a
from . import model
from . import tasks
from . import util      as u
from . import widgets   as w

log = logging.getLogger(__name__)


def gui():
    ltv = tasks.get_ltv(auth=False)
    languages  = [''] + [v['name'] for v in ltv.get_languages().values()]
    categories = [''] + [c.name.title() for c in model.Category]
    subtitles  = [f'Subtitle {i}' for i in range(1, 21)]
    window = w.Window(title = a.__project__,
                      icon  = u.get_resource_path(a.__icon__))
    window.set_layout(
        [
            [
                [w.FilePicker('Video &File', span=(1, 3))],
                [w.ComboBox('Lang&uage', span=(1, 3), choices=languages)],
                [w.Text('&Title', span=(1, 3))],
                [w.ComboBox('C&ategory', choices=categories), w.Text('&Year')],
                [w.Text('Seaso&n'), w.Text('&Episode')],
            ],
            [
                [w.Button('Searc&h')],
                [w.ListBox('', key='subtitles', choices=subtitles)],
            ],
            [
                [w.Button('Confi&gure...'),
                 w.CheckBox('C&lean', value=True),
                 w.Button('&Download'),
                 w.Button('&Cancel')]
            ],
        ],
        fixed_rows=(0, 2)
    )
    window.run()
