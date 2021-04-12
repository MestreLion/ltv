# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    GUI Framework Wrappers

A.K.A. "Reinventing PySimpleGui"
"""

import logging
import os
import string
import unicodedata

import wx


log = logging.getLogger(__name__)


class Window:
    PADDING = 5
    MARGIN  = 2 * PADDING
    ORIENT  = wx.VERTICAL

    def __init__(self, layout=None, **kw_frame):
        self._app = wx.App()

        icon = kw_frame.pop('icon')
        self._window = wx.Frame(parent=None, **kw_frame)
        if icon is not None and os.path.exists(icon):
            self._window.SetIcon(wx.Icon(icon))

        self.widgets = {}
        if layout is not None:
            self.widgets = self.set_layout(layout)

    def run(self):
        self._window.Show()
        self._app.MainLoop()

    def set_layout(self, layout,
                   margin=MARGIN, padding=PADDING,
                   rows=0, cols=1, fixed_rows=(), fixed_cols=(),
                   **kw_outer):
        if len(layout) and len(layout[0]) and isinstance(layout[0][0], Widget):
            layout = [layout]

        window = self._window
        marginsizer = wx.BoxSizer()
        outersizer = wx.FlexGridSizer(rows, cols, gap=(padding, padding), **kw_outer)

        for g, group in enumerate(layout):
            log.debug("Panel %s: %s rows", g, len(group))
            panel = wx.Panel(window)
            sizer = wx.GridBagSizer(vgap=padding, hgap=padding)
            for r, row in enumerate(group):
                c = 0
                for widget in row:
                    log.debug("%s: %s", (r, c), widget)
                    if not widget:
                        c += 1
                        continue
                    c, w = widget.add(panel, sizer, (r, c))
                    if widget.key:
                        self.widgets[widget.key] = w
            panel.SetSizerAndFit(sizer)
            outersizer.Add(panel, flag=wx.EXPAND)

        for dim in ('row', 'col'):
            tdim = dim.title()
            for x in range(getattr(outersizer, f'GetEffective{tdim}sCount')()):
                if x not in locals()[f'fixed_{dim}s']:
                    getattr(outersizer, f'AddGrowable{tdim}')(x)

        marginsizer.Add(outersizer, proportion=1, flag=wx.EXPAND | wx.ALL, border=margin)
        window.SetSizerAndFit(marginsizer)

        for k in self.widgets:
            log.debug("%r\t%s", k,  self.widgets[k])

        return self.widgets


class Widget:
    _WIDGET = None
    _SFLAG  = 0
    _WKW    = {}
    _label_map = str.maketrans('', '', string.whitespace + string.punctuation.replace('_', ''))
    _grid_keys = ('span', 'flag', 'border')

    def __init__(self, label="", key='', **kw):
        if not self._WIDGET:
            raise NotImplementedError
        self.label = label
        self.key = key or kw.pop('name', None) or self._identifier(self.label)
        self.kw_sizer = {k: kw.pop(k) for k in kw.copy() if k in self._grid_keys}
        self.kw_widget = kw
        self.widget = None

    @classmethod
    def _identifier(cls, s):
        s = s.strip().replace(' ', '_')
        s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode()
        return ''.join(c for c in s if c.isalnum() or c == '_').lower()

    def add(self, parent, grid, pos):
        raise NotImplementedError

    def _create_widget(self, parent, **kw):
        self.kw_widget.update(kw)
        return self._WIDGET(parent, name=self.key, **self.kw_widget)

    def _add_to_sizer(self, sizer, pos, **kw):
        _, col = pos
        self.kw_sizer.update(kw)
        self.kw_sizer['flag'] = self.kw_sizer.get('flag', 0) | self._SFLAG | wx.EXPAND
        sizer.Add(self.widget, pos=pos, **self.kw_sizer)
        if not sizer.IsColGrowable(col):
            sizer.AddGrowableCol(col)
        return col + 1

    def __repr__(self):
        return '<{}({!r}, key={!r})>'.format(self.__class__.__name__,
                                             self.label, self.key)


class LabeledWidget(Widget):
    def add(self, parent, sizer, pos):
        self.widget = self._create_widget(parent, label=self.label)
        col = self._add_to_sizer(sizer, pos)
        return col, self.widget


class Button(LabeledWidget):
    _WIDGET = wx.Button


class CheckBox(LabeledWidget):
    _WIDGET = wx.CheckBox

    def _create_widget(self, parent, **kw):
        self.kw_widget.update(kw)
        value = self.kw_widget.pop('value', False)
        widget = super()._create_widget(parent)
        widget.SetValue(value)  # Can't believe this is not in constructor!
        return widget


class OuterLabelWidget(Widget):
    def add(self, parent, sizer, pos):
        row, col = pos
        if self.label:
            sizer.Add(wx.StaticText(parent, label=self.label), pos=(row, col),
                      flag=wx.ALIGN_CENTER_VERTICAL)
            col += 1
        self.widget = self._create_widget(parent)
        col = self._add_to_sizer(sizer, (row, col))
        return col, self.widget


class Text(OuterLabelWidget):
    _WIDGET = wx.TextCtrl


class ListBox(OuterLabelWidget):
    _WIDGET = wx.ListBox

    def _create_widget(self, parent, **kw):
        widget = super()._create_widget(parent, **kw)
        widget.SetInitialSize((-1, 210))  # from GetEffectiveMinSize() when 8+ items
        return widget

    def _add_to_sizer(self, sizer, pos, **kw):
        col = super()._add_to_sizer(sizer, pos, **kw)
        row, _ = pos
        if not sizer.IsRowGrowable(row):
            sizer.AddGrowableRow(row)
        return col


class ComboBox(OuterLabelWidget):
    _WIDGET = wx.Choice


class FilePicker(OuterLabelWidget):
    _WIDGET = wx.FilePickerCtrl
