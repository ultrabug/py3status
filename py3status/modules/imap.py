# -*- coding: utf-8 -*-
"""
Display number of unread messages from IMAP account.

Configuration parameters:
    allow_urgent: display urgency on unread messages (default False)
    cache_timeout: refresh interval for this module (default 60)
    criterion: status of emails to check for (default 'UNSEEN')
    debug: log warnings (default False)
    format: display format for this module (default 'Mail: {unseen}')
    hide_if_zero: hide this module when no new mail (default False)
    mailbox: name of the mailbox to check (default 'INBOX')
    password: login password (default None)
    port: number to use (default '993')
    read_timeout: timeout for read(2) syscalls (default 5)
    security: login authentication method: 'ssl' or 'starttls'
        (startssl needs python 3.2 or later) (default 'ssl')
    server: server to connect (default None)
    use_idle: use IMAP4 IDLE instead of polling; requires compatible
        server; uses cache_timeout for IDLE's timeout; will auto detect
        when set to None (default None)
    user: login user (default None)

Format placeholders:
    {unseen} number of unread emails

Color options:
    color_new_mail: use color when new mail arrives, default to color_good

@author obb, girst

SAMPLE OUTPUT
{'full_text': 'Mail: 36', 'color': '#00FF00'}
"""
import imaplib
from threading import Thread
from time import sleep
from ssl import create_default_context
from socket import error as socket_error

STRING_UNAVAILABLE = "N/A"
NO_DATA_YET = -1


class Py3status:
    """
    """

    # available configuration parameters
    allow_urgent = False
    cache_timeout = 60
    criterion = "UNSEEN"
    debug = False
    format = "Mail: {unseen}"
    hide_if_zero = False
    mailbox = "INBOX"
    password = None
    port = "993"
    read_timeout = 5
    security = "ssl"
    server = None
    use_idle = None
    user = None

    class Meta:
        deprecated = {
            "rename": [
                {
                    "param": "new_mail_color",
                    "new": "color_new_mail",
                    "msg": "obsolete parameter use `color_new_mail`",
                },
                {
                    "param": "imap_server",
                    "new": "server",
                    "msg": "obsolete parameter use `server`",
                },
            ]
        }

    def post_config_hook(self):
        # class variables:
        self.mail_count = NO_DATA_YET
        self.connection = None
        self.mail_error = None  # cannot throw self.py3.error from thread
        self.command_tag = (
            0
        )  # IMAPcommands are tagged, so responses can be matched up to requests
        self.idle_thread = Thread()

        if self.security not in ["ssl", "starttls"]:
            raise ValueError("Unknown security protocol")

    def imap(self):
        # I -- acquire mail_count
        if self.use_idle is not False:
            if not self.idle_thread.is_alive():
                sleep(
                    self.read_timeout
                )  # rate-limit thread-restarting (when network is offline)
                self.idle_thread = Thread(target=self._get_mail_count)
                self.idle_thread.daemon = True
                self.idle_thread.start()
        else:
            self._get_mail_count()
        response = {"cached_until": self.py3.time_in(self.cache_timeout)}
        if self.mail_error is not None:
            self.py3.log(self.mail_error, level=self.py3.LOG_ERROR)
            self.py3.error(self.mail_error)
            self.mail_error = None

        # II -- format response
        response["full_text"] = self.py3.safe_format(
            self.format, {"unseen": self.mail_count}
        )

        if self.mail_count is None:
            response["color"] = (self.py3.COLOR_BAD,)
            response["full_text"] = self.py3.safe_format(
                self.format, {"unseen": STRING_UNAVAILABLE}
            )
        elif self.mail_count == NO_DATA_YET:
            response["full_text"] = ""
        elif self.mail_count == 0 and self.hide_if_zero:
            response["full_text"] = ""
        elif self.mail_count > 0:
            response["color"] = self.py3.COLOR_NEW_MAIL or self.py3.COLOR_GOOD
            response["urgent"] = self.allow_urgent

        return response

    def _check_if_idle(self, connection):
        supports_idle = "IDLE" in connection.capabilities

        self.use_idle = supports_idle
        self.py3.log("Will use {}".format("idling" if self.use_idle else "polling"))
        if self.use_idle and not supports_idle:
            self.py3.error("Server does not support IDLE")

    def _connection_ssl(self):
        connection = imaplib.IMAP4_SSL(self.server, int(self.port))
        return connection

    def _connection_starttls(self):
        connection = imaplib.IMAP4(self.server, int(self.port))
        connection.starttls(create_default_context())
        return connection

    def _connect(self):
        if self.security == "ssl":
            self.connection = self._connection_ssl()
        elif self.security == "starttls":
            self.connection = self._connection_starttls()
        if self.use_idle is None:
            self._check_if_idle(self.connection)

        # trigger a socket.timeout if any IMAP request isn't completed in time:
        self.connection.socket().settimeout(self.read_timeout)

    def _disconnect(self):
        try:
            if self.connection is not None:
                if self.connection.state == "SELECTED":
                    self.connection.close()
                self.connection.logout()
        except:  # noqa e722
            pass
        finally:
            self.connection = None

    def _idle(self):
        """
        since imaplib doesn't support IMAP4r1 IDLE, we'll do it by hand
        """
        socket = None

        try:
            # build a new command tag (Xnnn) as bytes:
            self.command_tag = (self.command_tag + 1) % 1000
            command_tag = b"X" + bytes(str(self.command_tag).zfill(3), "ascii")

            # make sure we have selected anything before idling:
            directories = self.mailbox.split(",")
            self.connection.select(directories[0])

            socket = self.connection.socket()

            # send IDLE command and check response:
            socket.write(command_tag + b" IDLE\r\n")
            try:
                response = socket.read(4096).decode("ascii")
            except socket_error:
                raise imaplib.IMAP4.abort("Server didn't respond to 'IDLE' in time")
            if not response.lower().startswith("+ idling"):
                raise imaplib.IMAP4.abort("While initializing IDLE: " + str(response))

            # wait for changes (EXISTS, EXPUNGE, etc.):
            socket.settimeout(self.cache_timeout)
            while True:
                try:
                    response = socket.read(4096).decode("ascii")
                    if response.upper().startswith("* OK"):
                        continue  # ignore '* OK Still here'
                    else:
                        break
                except socket_error:  # IDLE timed out
                    break

        finally:  # terminate IDLE command gracefully
            if socket is None:
                return

            socket.settimeout(self.read_timeout)
            socket.write(b"DONE\r\n")  # important! Can't query IMAP again otherwise
            try:
                response = socket.read(4096).decode("ascii")
            except socket_error:
                raise imaplib.IMAP4.abort("Server didn't respond to 'DONE' in time")

            # sometimes, more messages come in between reading and DONEing; so read them again:
            if response.startswith("* "):
                try:
                    response = socket.read(4096).decode("ascii")
                except socket_error:
                    raise imaplib.IMAP4.abort(
                        "Server sent more continuations, but no 'DONE' ack"
                    )

            expected_response = (command_tag + b" OK").decode("ascii")
            if not response.lower().startswith(expected_response.lower()):
                raise imaplib.IMAP4.abort("While terminating IDLE: " + response)

    def _get_mail_count(self):
        try:
            while True:
                if self.connection is None:
                    self._connect()
                if self.connection.state == "NONAUTH":
                    self.connection.login(self.user, self.password)

                tmp_mail_count = 0
                directories = self.mailbox.split(",")

                for directory in directories:
                    self.connection.select(directory)
                    unseen_response = self.connection.search(None, self.criterion)
                    mails = unseen_response[1][0].split()
                    tmp_mail_count += len(mails)

                self.mail_count = tmp_mail_count

                if self.use_idle:
                    self.py3.update()
                    self._idle()
                else:
                    return
        except (socket_error, imaplib.IMAP4.abort, imaplib.IMAP4.readonly) as e:
            if self.debug:
                self.py3.log(
                    "Recoverable error - " + str(e), level=self.py3.LOG_WARNING
                )
            self._disconnect()
        except (imaplib.IMAP4.error, Exception) as e:
            self.mail_error = "Fatal error - " + str(e)
            self._disconnect()
            self.mail_count = None
        finally:
            self.py3.update()  # to propagate mail_error


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
