from __future__ import unicode_literals
from __future__ import print_function

import argparse
import logging
import sys

from . import __version__
from . import subcommand
from .client import Client
from .subcommands import report, run
from . import constants

log = logging.getLogger('dpagent')

# Map log levels on to integer values
_logging_level_names = {
    'NOTSET': 0,
    'DEBUG': 10,
    'INFO': 20,
    'WARN': 30,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}


class App(object):
    """Dataplicty Agent"""

    def __init__(self):
        self.subcommands = {
            name: cls(self)
            for name, cls in subcommand.registry.items()
        }

    def _make_arg_parser(self):
        parser = argparse.ArgumentParser(
            "dpagent",
            description=self.__doc__
        )

        parser.add_argument('-v', '--version', action="version", version=__version__,
                            help="Display version and exit")
        parser.add_argument('--log-level', metavar='LEVEL', default='INFO',
                            help="Set log level (INFO or WARNING or ERROR or DEBUG)")
        parser.add_argument('-d', '--debug', action="store_true", dest="debug", default=False,
                            help="Enables debug output")
        parser.add_argument('-c', '--conf', metavar="PATH", dest="conf", default=None,
                            help="the location of the conf file to load")
        parser.add_argument('-s', '--server-url', metavar="URL", dest="server_url", default=None,
                            help="URL of dataplicity.com api")
        parser.add_argument('-q', '--quiet', action="store_true", default=False,
                            help="hide output")

        subparsers = parser.add_subparsers(title='available sub-commands',
                                           dest="subcommand",
                                           help="sub-command help")

        for name, _subcommand in self.subcommands.items():
            subparser = subparsers.add_parser(name,
                                              help=_subcommand.help,
                                              description=getattr(_subcommand, '__doc__', None))
            _subcommand.add_arguments(subparser)
        return parser

    def _init_logging(self):
        if self.args.quiet:
            return

        format = "%(asctime)s:%(name)s:%(levelname)s: %(message)s"
        datefmt = "[%d/%b/%Y %H:%M:%S]"

        try:
            level = _logging_level_names[self.args.log_level.upper()]
        except IndexError:
            self.error('invalid log level')

        logging.basicConfig(format=format,
                            datefmt=datefmt,
                            level=level)

    def make_client(self):
        path = self.args.conf or constants.CONF_PATH

        client = Client(
            path,
            rpc_url=self.args.server_url
        )
        return client

    def error(self, msg, code=-1):
        log.critical('app exit ({%s}) code={%s}', msg, code)
        sys.stderr.write(msg + '\n')
        sys.exit(code)

    def run(self):
        parser = self._make_arg_parser()
        args = self.args = parser.parse_args(sys.argv[1:])
        self._init_logging()
        log.debug('ready')

        subcommand = self.subcommands[args.subcommand]
        subcommand.args = args

        try:
            return subcommand.run() or 0
        except Exception as e:
            if self.args.debug:
                raise
            #sys.stderr.write(str(e) + '\n')
            sys.stderr.write("(dpagent {}) {}\n".format(__version__, e))
            cmd = sys.argv[0].rsplit('/', 1)[-1]
            debug_cmd = ' '.join([cmd, '--debug'] + sys.argv[1:])
            sys.stderr.write("(run '{}' for a full traceback)\n".format(debug_cmd))
            return -1



def main():
    """Dataplicity Agent entry point."""
    return_code = App().run() or 0
    log.debug('exit with code %s', return_code)
    sys.exit(return_code)