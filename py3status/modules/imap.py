"""
Display number of unread messages from IMAP account.

Configuration parameters:
    allow_urgent: display urgency on unread messages (default False)
    auth_scope: scope to use with OAuth2 (default 'https://mail.google.com/')
    auth_token: path to where the pickled access/refresh token will be saved
        after successful credential authorization.
        (default '~/.config/py3status/imap_auth_token.pickle')
    cache_timeout: refresh interval for this module (default 60)
    client_secret: the path to the client secret file with OAuth 2.0
        credentials (if None then OAuth not used) (default None)
    criterion: status of emails to check for (default 'UNSEEN')
    debug: log warnings (default False)
    degraded_when_stale: color as degraded when updating failed (default True)
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

OAuth:
    OAuth2 will be used for authentication instead of a password if the
    client_secret path is set.

    To create a client_secret for your Google account, visit
    https://console.developers.google.com/ and create an "OAuth client ID" from
    the credentials tab.

    This client secret enables the app (in this case, the IMAP py3status module)
    to request access to a user's email. Therefore the client secret doesn't
    have to be for the same Google account as the email account being accessed.

    When the IMAP module first tries to access your email account a browser
    window will open asking for authorization to access your email.
    After authorization is complete, an access/refresh token will be saved to
    the path configured in auth_token.

    Requires: Using OAuth requires the google-auth and google-auth-oauthlib
    libraries to be installed.

    Note: the same client secret file can be used as with the py3status Google
    Calendar module.

@author obb, girst

SAMPLE OUTPUT
{'full_text': 'Mail: 36', 'color': '#00FF00'}
"""
import imaplib
from threading import Thread
from time import sleep
from ssl import create_default_context
from socket import setdefaulttimeout, error as socket_error
from pathlib import Path

STRING_UNAVAILABLE = "N/A"
NO_DATA_YET = -1


class Py3status:
    """"""

    # available configuration parameters
    allow_urgent = False
    auth_scope = "https://mail.google.com/"
    auth_token = "~/.config/py3status/imap_auth_token.pickle"
    cache_timeout = 60
    client_secret = None
    criterion = "UNSEEN"
    debug = False
    degraded_when_stale = True
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
        self.network_error = None
        self.command_tag = (
            0  # IMAPcommands are tagged, so responses can be matched up to requests
        )
        self.idle_thread = Thread()

        if self.client_secret:
            self.client_secret = Path(self.client_secret).expanduser()
        self.auth_token = Path(self.auth_token).expanduser()

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
        if self.network_error is not None and self.degraded_when_stale:
            response["color"] = self.py3.COLOR_DEGRADED

        return response

    def _check_if_idle(self, connection):
        supports_idle = "IDLE" in connection.capabilities

        self.use_idle = supports_idle
        self.py3.log("Will use {}".format("idling" if self.use_idle else "polling"))
        if self.use_idle and not supports_idle:
            self.py3.error("Server does not support IDLE")

    def _get_creds(self):
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.auth.exceptions import TransportError
        import pickle

        self.creds = None

        # Open pickle file with access and refresh tokens if it exists
        if self.auth_token.exists():
            with self.auth_token.open("rb") as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            try:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    # Credentials expired but contain refresh token
                    self.creds.refresh(Request())
                else:
                    # No valid credentials so open authorisation URL in browser
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secret, [self.auth_scope]
                    )
                    self.creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with self.auth_token.open("wb") as token:
                    pickle.dump(self.creds, token)
            except TransportError as e:
                # Treat the same as a socket_error
                raise socket_error(e)

    def _connection_ssl(self):
        if self.client_secret:
            # Use OAUTH
            self._get_creds()
        setdefaulttimeout(self.read_timeout)
        connection = imaplib.IMAP4_SSL(self.server, int(self.port))
        return connection

    def _connection_starttls(self):
        setdefaulttimeout(self.read_timeout)
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
            # Dovecot will responde with "+ idling", courier will return "+ entering idle mode"
            # RFC 2177 (https://tools.ietf.org/html/rfc2177) only requires the "+" character.
            if not response.lower().startswith("+"):
                raise imaplib.IMAP4.abort(f"While initializing IDLE: {response}")

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
        retry_counter = 0
        retry_max = 3
        while True:
            try:
                if self.connection is None:
                    self._connect()
                if self.connection.state == "NONAUTH":
                    if self.client_secret:
                        # Authenticate using OAUTH
                        auth_string = "user={}\1auth=Bearer {}\1\1".format(
                            self.user, self.creds.token
                        )
                        self.connection.authenticate("XOAUTH2", lambda x: auth_string)
                    else:
                        # Login with user and password
                        self.connection.login(self.user, self.password)

                tmp_mail_count = 0
                directories = self.mailbox.split(",")

                for directory in directories:
                    self.connection.select(directory)
                    unseen_response = self.connection.search(None, self.criterion)
                    mails = unseen_response[1][0].split()
                    tmp_mail_count += len(mails)

                self.mail_count = tmp_mail_count
                self.network_error = None

                if self.use_idle:
                    self.py3.update()
                    self._idle()
                    retry_counter = 0
                else:
                    return
            except (socket_error, imaplib.IMAP4.abort, imaplib.IMAP4.readonly) as e:
                if "didn't respond to 'DONE'" in str(e) or isinstance(e, socket_error):
                    self.network_error = str(e)
                    error_type = "Network"
                else:
                    error_type = "Recoverable"
                    # Note: we don't reset network_error, as we want this to persist
                    # until we either run into a permanent error or successfully receive
                    # another response from the IMAP server.

                if self.debug:
                    self.py3.log(
                        f"{error_type} error - {e}", level=self.py3.LOG_WARNING,
                    )
                self._disconnect()

                retry_counter += 1
                if retry_counter <= retry_max:
                    if self.debug:
                        self.py3.log(
                            f"Retrying ({retry_counter}/{retry_max})",
                            level=self.py3.LOG_INFO,
                        )
                    continue
                break
            except (imaplib.IMAP4.error, Exception) as e:
                self.mail_error = f"Fatal error - {e}"
                self._disconnect()
                self.mail_count = None

                retry_counter += 1
                if retry_counter <= retry_max:
                    if self.debug:
                        self.py3.log(
                            "Will retry after 60 seconds ({}/{})".format(
                                retry_counter, retry_max
                            ),
                            level=self.py3.LOG_INFO,
                        )
                    sleep(60)
                    continue
                break
            finally:
                self.py3.update()  # to propagate mail_error


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
