"""Textual interface for the ZK Authentication demo.

The UI stays deliberately thin: it forwards user actions to the network
layer (client/network.py) and the server (server/server.py), and streams
the server's log records into a live panel. It performs no cryptography
itself and never touches the crypto modules directly -- keeping the
layered architecture intact.
"""

import asyncio
import logging

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    OptionList,
    RichLog,
    Static,
)

from client.network import ServerConnection
from client.wallet import Wallet
from server.server import Server

RUNS = 3
SERVER_LOGGER = "zk.server"


class LogHandler(logging.Handler):
    """Bridges stdlib logging records onto the app's asyncio queue."""

    def __init__(self):
        super().__init__(level=logging.INFO)
        self.setFormatter(
            logging.Formatter(
                "%(asctime)s  %(levelname)-7s %(message)s", datefmt="%H:%M:%S"
            )
        )
        self.queue = asyncio.Queue()

    def emit(self, record):
        self.queue.put_nowait(self.format(record))


class BaseModal(ModalScreen):
    """Shared styling for the pop-up screens."""

    CSS = """
    Screen {
        align: center middle;
    }
    Vertical {
        width: 60;
        border: solid $primary;
        background: $panel;
        padding: 1 2;
    }
    Label {
        margin: 0 0 1 0;
        content-align: center middle;
    }
    Input {
        margin: 0 0 1 0;
    }
    #actions {
        height: auto;
        margin-top: 1;
    }
    """


class RegisterModal(BaseModal):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("[bold cyan]Register a User[/bold cyan]"),
            Input(placeholder="username", id="username"),
            Container(
                Button("Register", variant="primary", id="go"),
                Button("Cancel", id="cancel"),
                id="actions",
            ),
            id="register-form",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        username = self.query_one("#username", Input).value.strip()
        if event.button.id == "cancel" or not username:
            self.app.pop_screen()
            return
        self.app.run_worker(
            self._register(username), group="auth", exclusive=True
        )

    async def _register(self, username: str) -> None:
        try:
            public_key = await self.app.connection.register(username)
        except (ValueError, RuntimeError, ConnectionError) as err:
            self.app.notify(str(err), severity="error", timeout=3)
            return
        self.app.notify(f"Registered {username!r} (y={public_key})", timeout=3)
        self.app.pop_screen()


class LoginModal(BaseModal):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("[bold cyan]Authenticate[/bold cyan]"),
            Input(placeholder="username", id="username"),
            Container(
                Button("Login", variant="primary", id="go"),
                Button("Cancel", id="cancel"),
                id="actions",
            ),
            id="login-form",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        username = self.query_one("#username", Input).value.strip()
        if event.button.id == "cancel" or not username:
            self.app.pop_screen()
            return
        self.app.run_worker(
            self._login(username), group="auth", exclusive=True
        )

    async def _login(self, username: str) -> None:
        try:
            accepted = await self.app.connection.authenticate(username, rounds=RUNS)
        except (ValueError, RuntimeError, ConnectionError) as err:
            self.app.notify(str(err), severity="error", timeout=3)
            return
        ok = accepted == RUNS
        self.app.notify(
            f"{username!r}: {'authenticated' if ok else 'REJECTED'} "
            f"({accepted}/{RUNS})",
            severity="information" if ok else "error",
            timeout=3,
        )
        self.app.pop_screen()


class AboutModal(BaseModal):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("[bold cyan]ZK Authentication[/bold cyan]"),
            Static(
                "Schnorr Sigma Protocol demo\n"
                "The server verifies you know the\n"
                "secret key -- but never learns it.",
                id="about-text",
            ),
            Container(Button("Close", id="close"), id="actions"),
            id="about-form",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


class ZKAuth(App):
    TITLE = "ZK Authentication"

    CSS = """
    Screen {
        background: $surface;
    }
    #brand-header {
        width: 1fr;
        height: 3;
        content-align: center middle;
        background: $boost;
        border-bottom: solid $primary;
        padding: 1 2;
        color: $text;
    }
    #content {
        height: 1fr;
    }
    #menu-container {
        height: 3fr;
        padding: 1 4;
    }
    #menu {
        width: 100%;
        height: 100%;
        border: solid $primary;
        background: $panel;
        color: $text;
    }
    OptionList {
        color: $text;
    }
    #server-log {
        height: 2fr;
        min-height: 5;
        border-top: solid $primary;
        background: $panel;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.wallet = Wallet()
        self.server = Server(
            logger=logging.getLogger(SERVER_LOGGER),
            params_file="data/parameters.json",
        )
        self.connection = ServerConnection(
            host=self.server.host, port=self.server.port, wallet=self.wallet
        )
        self.log_handler = LogHandler()
        server_logger = logging.getLogger(SERVER_LOGGER)
        server_logger.setLevel(logging.INFO)
        server_logger.addHandler(self.log_handler)
        self.server_task = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static("[bold cyan]ZK[/bold cyan] Authentication", id="brand-header")
        yield Vertical(
            Container(
                OptionList(
                    "Register User",
                    "Login",
                    "Start Server",
                    "Stop Server",
                    "About",
                    "Exit",
                    id="menu",
                ),
                id="menu-container",
            ),
            RichLog(
                id="server-log", highlight=True, markup=False, wrap=True, max_lines=500
            ),
            id="content",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._drain_logs(), group="logs")

    async def _drain_logs(self) -> None:
        log_widget = self.query_one("#server-log", RichLog)
        while True:
            message = await self.log_handler.queue.get()
            log_widget.write(message)
            log_widget.scroll_end(animate=False)

    # --- menu actions -------------------------------------------------

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        selected = event.option.prompt

        if selected == "Register User":
            self.push_screen(RegisterModal())
        elif selected == "Login":
            self.push_screen(LoginModal())
        elif selected == "Start Server":
            self._start_server()
        elif selected == "Stop Server":
            self._stop_server()
        elif selected == "About":
            self.push_screen(AboutModal())
        elif selected == "Exit":
            self.exit()

    def _start_server(self) -> None:
        if self.server.running:
            self.notify("Server is already running", timeout=2)
            return
        self.notify(
            f"Starting server on {self.server.host}:{self.server.port}...", timeout=2
        )
        self.server_task = self.run_worker(
            self._run_server(), group="server", exit_on_error=False
        )

    def _stop_server(self) -> None:
        if not self.server.running:
            self.notify("Server is not running", timeout=2)
            return
        self.run_worker(self._shutdown_server(), group="server", exit_on_error=False)

    async def _run_server(self) -> None:
        try:
            await self.server.start()
            await self.connection.connect()
            self.notify("Server ready", timeout=2)
        except Exception as err:
            self.notify(f"Server failed to start: {err}", severity="error", timeout=3)
            await self.server.stop()
            return
        await self.server.serve()

    async def _shutdown_server(self) -> None:
        # Close our client socket first: Server.wait_closed() waits for all
        # active connections to finish, so the server cannot shut down while
        # the TUI's own connection is still open.
        await self.connection.close()
        await self.server.stop()
        if self.server_task is not None:
            self.server_task.cancel()
            self.server_task = None
        self.notify("Server stopped", timeout=2)


if __name__ == "__main__":
    ZKAuth().run()