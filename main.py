from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, OptionList, Static, Button, MaskedInput
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.reactive import reactive


class BrandHeader(Static):
    """Custom header with branding"""
    
    def render(self) -> str:
        return "[bold cyan]ZK[/bold cyan] Authentication"

from textual.app import App, ComposeResult
from textual.widgets import Label, MaskedInput


class MaskedInputApp():
    
    CSS = """
    MaskedInput.-valid {
        border: tall $success 60%;
    }
    MaskedInput.-valid:focus {
        border: tall $success;
    }
    MaskedInput {
        margin: 1 1;
    }
    Label {
        margin: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Enter a valid credit card number.")
        yield MaskedInput(
            template="9999-9999-9999-9999;0",  
        )



class AboutScreen(ModalScreen):
    """Modal screen for About information"""
    
    CSS = """
    Screen {
        align: center middle;
    }

    #about-title {
        width: 100%;
        height: 1;
        content-align: center middle;
        color: $text;
    }

    #about-content {
        align-ceter: True;
        width: 100%;
        height: auto;
        color: $text;
        margin: 1 0;
    }

    #close-button {
        width: 100%;
        height: 1;
        margin-top: 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Container(
            Static("[bold cyan]ZK Authentication[/bold cyan]", id="about-title"),
            Static(
                "Version: 1.0\n\n"
                "Zero-Knowledge Authentication System\n\n"
                "A modern, minimal authentication platform\n"
                "with zero-knowledge proof capabilities.\n\n"
                "© 2024 ZK Auth. All rights reserved.",
                id="about-content"
            ),
            Button("Close", variant="primary", id="close-button"),
            id="about-box"
        )

    def on_button_pressed(self) -> None:
        self.app.pop_screen()



class UserRegister(ModalScreen):
    """Modal screen for User Registration"""
    
    CSS = """
    Screen {
        align: center middle;
    }

    #about-title {
        width: 100%;
        height: 1;
        content-align: center middle;
        color: $text;
    }

    #about-content {
        align-ceter: True;
        width: 100%;
        height: auto;
        color: $text;
        margin: 1 0;
    }

    #close-button {
        width: 100%;
        height: 1;
        margin-top: 2;
    }
    """

    def compose(self) -> ComposeResult:

        yield 
        yield Container(
            Static("[bold cyan]ZK Authentication[/bold cyan]", id="about-title"),
            Static(
                "Version: 1.0\n\n"
                "Zero-Knowledge Authentication System\n\n"
                "A modern, minimal authentication platform\n"
                "with zero-knowledge proof capabilities.\n\n"
                "© 2024 ZK Auth. All rights reserved.",
                id="about-content"
            ),
            Button("Close", variant="primary", id="close-button"),
            id="about-box"
        )

    def on_button_pressed(self) -> None:
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

    #menu-container {
        width: 1fr;
        height: 1fr;
        padding: 2 4;
    }

    #menu {
        width: 100%;
        height: auto;
        border: solid $primary;
        background: $panel;
        color: $text;
    }

    OptionList {
        color: $text;
    }

    #footer {
        dock: bottom;
        height: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        
        yield BrandHeader(id="brand-header")
        
        yield Container(
            OptionList(
                "Register User",
                "Login",
                "Start Server",
                "Configuration",
                "About",
                "Exit",
                id="menu"
            ),
            id="menu-container"
        )

        yield Footer()

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        selected = event.option.prompt

        if selected == "Register User":
            self.notify("📝 Opening user registration...", timeout=2)
            self.app.push_screen(UserRegister())

        elif selected == "Login":
            self.notify("🔐 Opening login...", timeout=2)

        elif selected == "Start Server":
            self.notify("🚀 Starting server...", timeout=2)

        elif selected == "Configuration":
            self.notify("⚙️ Opening configuration...", timeout=2)

        elif selected == "About":
            self.app.push_screen(AboutScreen())

        elif selected == "Exit":
            self.exit()


if __name__ == "__main__":
    ZKAuth().run()