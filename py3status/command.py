import argparse
import glob
import json
import os
import socket
import sys
import threading

from py3status.version import version

SERVER_ADDRESS = '/tmp/py3status_uds'
MAX_SIZE = 1024

BUTTONS = {
    'leftclick': 1,
    'middleclick': 2,
    'rightclick': 3,
    'scrollup': 4,
    'scrolldown': 5,
}


class CommandRunner:
    """
    Encapsulates the remote commands that are available to run.
    """

    def __init__(self, py3_wrapper):
        self.debug = py3_wrapper.config['debug']
        self.py3_wrapper = py3_wrapper

    def find_modules(self, requested_names):
        """
        find the module(s) given the name(s)
        """
        found_modules = set()
        for requested_name in requested_names:
            is_instance = ' ' in requested_name

            for module_name, module in self.py3_wrapper.output_modules.items():
                if module['type'] == 'py3status':
                    name = module['module'].module_nice_name
                else:
                    name = module['module'].module_name
                if is_instance:
                    if requested_name == name:
                        found_modules.add(module_name)
                else:
                    if requested_name == name.split(' ')[0]:
                        found_modules.add(module_name)

        if self.debug:
            self.py3_wrapper.log('found %s' % found_modules)
        return found_modules

    def refresh(self, data):
        """
        refresh the module(s)
        """
        modules = data.get('module')
        # for i3status modules we have to refresh the whole i3status output.
        update_i3status = False
        for module_name in self.find_modules(modules):
            module = self.py3_wrapper.output_modules[module_name]
            if self.debug:
                self.py3_wrapper.log('refresh %s' % module)
            if module['type'] == 'py3status':
                module['module'].force_update()
            else:
                update_i3status = True
        if update_i3status:
            self.py3_wrapper.i3status_thread.refresh_i3status()

    def click(self, data):
        """
        send a click event to the module(s)
        """
        button = data.get('button')
        modules = data.get('module')

        for module_name in self.find_modules(modules):
            module = self.py3_wrapper.output_modules[module_name]
            if module['type'] == 'py3status':
                name = module['module'].module_name
                instance = module['module'].module_inst
            else:
                name = module['module'].name
                instance = module['module'].instance
            # our fake event, we do not know x, y so set to None
            event = {
                'y': None,
                'x': None,
                'button': button,
                'name': name,
                'instance': instance,
            }
            if self.debug:
                self.py3_wrapper.log(event)
            # trigger the event
            self.py3_wrapper.events_thread.dispatch_event(event)

    def run_command(self, data):
        """
        check the given command and send to the correct dispatcher
        """
        command = data.get('command')
        if self.debug:
            self.py3_wrapper.log('Running remote command %s' % command)
        if command == 'refresh':
            self.refresh(data)
        elif command == 'refresh_all':
            self.py3_wrapper.refresh_modules()
        elif command == 'click':
            self.click(data)


class CommandServer(threading.Thread):
    """
    Set up a Unix domain socket to allow commands to be sent to py3status
    instance.
    """

    def __init__(self, py3_wrapper):
        threading.Thread.__init__(self)

        self.debug = py3_wrapper.config['debug']
        self.py3_wrapper = py3_wrapper

        self.command_runner = CommandRunner(py3_wrapper)

        pid = os.getpid()

        server_address = '{}.{}'.format(SERVER_ADDRESS, pid)
        self.server_address = server_address

        # Make sure the socket does not already exist
        try:
            os.unlink(server_address)
        except OSError:
            if os.path.exists(server_address):
                raise

        # Create a UDS socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        sock.bind(server_address)

        if self.debug:
            self.py3_wrapper.log('Unix domain socket at %s' % server_address)

        # Listen for incoming connections
        sock.listen(1)
        self.sock = sock

    def kill(self):
        """
        Remove the socket as it is no longer needed.
        """
        try:
            os.unlink(self.server_address)
        except OSError:
            if os.path.exists(self.server_address):
                raise

    def run(self):
        """
        Main thread listen to socket and send any commands to the
        CommandRunner.
        """
        while True:
            try:
                data = None
                # Wait for a connection
                if self.debug:
                    self.py3_wrapper.log('waiting for a connection')

                connection, client_address = self.sock.accept()
                try:
                    if self.debug:
                        self.py3_wrapper.log('connection from')

                    data = connection.recv(MAX_SIZE)
                    if data:
                        data = json.loads(data.decode('utf-8'))
                        if self.debug:
                            self.py3_wrapper.log(u'received %s' % data)
                        self.command_runner.run_command(data)
                finally:
                    # Clean up the connection
                    connection.close()
            except Exception:
                if data:
                    self.py3_wrapper.log('Command error')
                    self.py3_wrapper.log(data)
                self.py3_wrapper.report_exception('command failed')


def command_parser():
    """
    build and return our command parser
    """

    parser = argparse.ArgumentParser(
        description='Send commands to running py3status instances'
    )
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        default=False,
        dest='verbose',
        help='print information',
    )
    parser.add_argument(
        '--version',
        action='store_true',
        default=False,
        dest='version',
        help='print version information',
    )

    subparsers = parser.add_subparsers(dest='command', help='commands')
    subparsers.required = False

    # Refresh
    refresh_parser = subparsers.add_parser(
        'refresh', help='refresh named module(s)'
    )
    refresh_parser.add_argument(nargs='+', dest='module', help='module(s)')

    # Click
    click_parser = subparsers.add_parser(
        'click', help='simulate click on named module(s)'
    )
    click_parser.add_argument(
        nargs='?',
        type=int,
        default=1,
        dest='button',
        help='button number to use',
    )
    click_parser.add_argument(nargs='+', dest='module', help='module(s)')

    # add shortcut commands for named buttons
    for k in sorted(BUTTONS, key=BUTTONS.get):
        click_parser = subparsers.add_parser(
            k, help='simulate %s on named module(s)' % k
        )

        click_parser.add_argument(nargs='+', dest='module', help='module(s)')

    return parser


def send_command():
    """
    Run a remote command.
    This is called via the py3status-command utility.

    We look for any uds sockets with the correct name prefix and send our
    command to all that we find.  This allows us to communicate with multiple
    py3status instances.
    """

    def output(msg):
        """
        print output if verbose is set.
        """
        if options.verbose:
            print(msg)

    parser = command_parser()
    options = parser.parse_args()

    # convert named buttons to click command for processing
    if options.command in BUTTONS:
        options.button = BUTTONS[options.command]
        options.command = 'click'

    if options.command == 'refresh' and 'all' in options.module:
        options.command = 'refresh_all'

    if options.version:
        import platform
        print('py3status-command version {} (python {})'.format(
            version, platform.python_version()
        ))
        sys.exit(0)

    if options.command:
        msg = json.dumps(vars(options))
    else:
        sys.exit(1)

    msg = msg.encode('utf-8')
    if len(msg) > MAX_SIZE:
        output('Message length too long, max length (%s)' % MAX_SIZE)

    # find all likely socket addresses
    uds_list = glob.glob('{}.[0-9]*'.format(SERVER_ADDRESS))

    output('message "%s"' % msg)
    for uds in uds_list:
        # Create a UDS socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        output('connecting to %s' % uds)
        try:
            sock.connect(uds)
        except socket.error:
            # this is a stale socket so delete it
            output('stale socket deleting')
            try:
                os.unlink(uds)
            except OSError:
                pass
            continue
        try:
            # Send data
            output('sending')
            sock.sendall(msg)

        finally:
            output('closing socket')
            sock.close()
