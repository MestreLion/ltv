# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2021 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Desktop Notifications

init()'ialization is optional, but allows one-time configuration of notifications'
`app_name` and `icon`, as well as initial enabled/disabled state.

The notify() wrapper is provided for automatic handling of class Notify as a singleton,
invoking its .send() method always on the same (possibly pre-configured) instance.

Besides desktop notifications this can also hook itself to the logging subsystem,
using a custom level, name and method, allowing a very convenient usage by modules
after init() by sending a notification and logging it at the same time.

Suggested usage, hooking to logging:
    - In __init__.py, main(), or a similar module/function:
        from . import notify
        notify.init(app_name, icon, ...)

    - In all modules: (You probably already do this. If not, you should!)
        import logging
        logger = logging.getLogger(__name__)

    - Sending a notification in any module, also logging it if applicable:
        # Notice you don't have to import notify,
        # you just invoke it like any other logging method!
        logger.notify(msg, args)

Suggested usage with no automated logging:
    - In __init__.py, main(), or a similar module/function:
        from . import notify
        notify.init(app_name, icon, hook_to_logging=False, ...)

    - Sending a notification in any module:
        from .notify import notify
        notify(msg, args)
"""

import collections
import logging
import pathlib
import os

# TODO: use dbus-next or pydbus!
try:
    import dbus
except ImportError:
    dbus = None


log = logging.getLogger(__name__)

_notifier = None


def init(app_name:str=None, icon:str=None, enabled:bool=True,
         hook_to_logging:bool=True, loglevel:int=0):
    """Initialize the singleton instance of class Notify, optionally hooking to logging

    <app_name>, <icon>, and <enabled> are used to create the Notify instance,
      see that class and its constructor for details and actual default values.

    If <hook_to_logging>, create a new logging.Logger.notify() method that logs
      to <loglevel> and additionally send a desktop notification.
    See _hook_to_logging() for details on logger.notify() usage and <loglevel> default.

    <enabled> affects only sending the desktop notifications, not their looging.
    """
    global _notifier
    if hook_to_logging:
        _hook_to_logging("notify", loglevel, "", notify, 'title', 'icon')
    _notifier = Notify(app_name=app_name, icon=icon, enabled=enabled)


def get_notifier():
    """Return the Notify singleton instance

    Might be used to change global notification parameters, such as
    app_name or enabled:
        from . import notify
        notify.get_notifier().enabled = False

    Will invoke init() with default values if this hasn't been done yet.
    """
    if not _notifier:
        init()
    return _notifier


def notify(body, *bodyargs, title=None, icon=None):
    """Wrapper to Notify.send() using the singleton instance."""
    get_notifier().send(body, *bodyargs, title=title, icon=icon)


class Notify:
    """Desktop Notifications using D-Bus

    Adheres to the Freedesktop.org Desktop Notifications Standard:
    https://specifications.freedesktop.org/notification-spec/latest/index.html

    Best used as a singleton via notify() wrapper or logger.notify(),
    but can also be used directly:
        notifier = Notify(...)
        notifier.send(...)
    """
    _DBUS_NAME = 'org.freedesktop.Notifications'
    _DBUS_PATH = '/org/freedesktop/Notifications'
    _ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'data', f"{__package__}.png")
    _interface = None

    def __init__(self, app_name:str=None, icon:str=None, enabled:bool=True):
        """Setup global notification parameters.

        <app_name> is required by the Freedesktop Standard, defaults to package name.
        <icon> sets the initial icon used by notifications. If blank, no icon is set.
            If None, defaults to 'data/<package>.png' in the directory of this
            module file, if such file exists. A lame default, we all agree.
        <enabled> acts as a master switch to enable or disable sending notifications.
        """
        self.app_name = app_name
        self.icon = (pathlib.Path(self._ICON_PATH).as_uri()
                     if (icon is None and os.path.isfile(self._ICON_PATH))
                     else icon)
        self.enabled = enabled

    def send(self, body:str, *bodyargs, title=None, icon=None):
        """Send a notification

        If <body> is empty, no notification is sent. It will be formatted with <bodyargs>
        using string interpolation (%-formatting), as in `str(body) % bodyargs`.

        Also, like logging module does, as a special case if <bodyargs> is a *single*
        argument that is a non-empty mapping (such as a dict), that mapping is used as if
        `bodyargs = bodyargs[0]`, resulting in a `str(body) % mapping` formatting.
        """
        if not (self.enabled and body):
            return

        if not dbus:
            log.warning("Notification support is not installed, disabling it...")
            self.enabled = False
            return

        # If icon is specified, save for later re-use
        if icon is not None:
            self.icon = icon

        def _check_dict(_args):
            # Check if a non-empty dict is the sole argument, like logging does
            if (_args and len(_args) == 1 and _args[0] and
                    isinstance(_args[0], collections.Mapping)):
                return _args[0]
            return _args

        # Set the DBus Notify arguments
        args = dict(
            app_name    = self.app_name or __package__,
            replaces_id = 0,
            icon        = self.icon or "",
            summary     = title,
            body        = str(body) % _check_dict(bodyargs),
            actions     = [],
            hints       = {'x-canonical-append': 'allowed'},  # merge if same summary
            timeout     = -1,  # server default
        )
        if args['summary'] is None:
            args['summary'] = args['app_name']

        # Use the same interface instance in all calls
        if not self._interface:
            self._interface = dbus.Interface(
                dbus.SessionBus().get_object(self._DBUS_NAME, self._DBUS_PATH),
                self._DBUS_NAME
            )

        # Send the notification
        self._interface.Notify(*args.values())  # No keyword arguments in python-dbus :(


def _hook_to_logging(name:str, level:int=0, titlesep:str='', func=None, *fkwargnames):
    """Create a custom logging level and its corresponding constant and Logger method

    <name> is used to name the level display name and module constant, both
      uppercased, and the Logger method, lowercased.
    <level>, the logging level, defaults to logging.INFO + 1, so it sits below
      WARNING and right above INFO.
    <titlesep> is the separator between the specially-handled `title` keyword
      argument and the formatted message, by default ' - ', used by the method
      when logging. See log_custom() below.
    <func> is an optional, extra function to be triggered by the Logger method
      after logging the message. It must have a signature compatible with
      (msg, *args, **kwargs), and will be invoked with the method's `msg`,
      its positional `args`, and keyword arguments named in <fkwargnames>.

    For example, considering this function:
        f = lambda _, *args, name='You', sep=', ': print(f"Hello {name}", *args, sep=sep)

    Calling _hook_to_logging("hello", 0, f, 'name', 'sep') creates:
        logging.HELLO = 21
        logging.Logger.hello(msg, *args, **kws)

    So you can use it in modules as:
        import logging
        logger = logging.getLogger(__name__)
        logger.hello("Call me %r or %r", 'Silva', 'MestreLion', name='Rodrigo')

    And it will:
        - Log "HELLO:Call me 'Silva' or 'MestreLion'", if logging level >= 21
        - Print "Hello Rodrigo, Silva, MestreLion", regardless of current level
    """
    def log_custom(self, msg:str, *args, **kws):
        """Custom Logger method

        As a logging method it works exactly like Logger.info() and siblings,
        using <args> to %-format <msg> and keyword args <kws> such as `exc_info`,
        and it logs only if enabled by current logging level.

        As a special case, it prepends the value of `title` keyword argument,
        if any, to the formatted message using the pre-configured `titlesep`.
        It also inspects the keyword `error`, evaluated as a boolean, and if
        True it logs using Logger.error() instead of the custom level.

        Apart from logging, if configured to do so this will also invoke `func`,
        regardless of current logging level, passing <msg>, the positional <args>
        and any pre-configured keyword args in `fkwargnames`. Note that `title`
        will *not* be automatically passed if not listed in `fkwargnames`!
        """
        # Prepend title, if any, to msg
        title = kws.get('title')  # do not pop it (yet), so it can be passed to func()
        logmsg = msg if not title else titlesep.join((title, msg))

        # Build all func() kwargs, pop'ing from kwargs
        fkws = {_k: kws.pop(_k) for _k in kws.copy() if _k in fkwargnames}

        # Pop remaining non-Logger kwargs
        error = kws.pop('error', False)
        kws.pop('title', None)

        # Log, either as ERROR (by invoking Logger.error()) or as the custom level
        if error:
            self.error(logmsg, *args, **kws)
        else:
            self.log(level, logmsg, *args, **kws)

        # Invoke func(), if any, even if logging is not enabled for custom level
        if func:
            func(msg, *args, **fkws)

    titlesep = titlesep or ' - '
    level = level or logging.INFO + 1          # default level is right above INFO
    logging.addLevelName(level, name.upper())  # display name for level
    setattr(logging, name.upper(), level)      # create the constant too
    setattr(logging.Logger, name.lower(), log_custom)  # hook to the Logger class
