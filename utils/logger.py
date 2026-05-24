from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.theme import Theme


# --- Rich Console Setup ---

custom_theme = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "bold red",
    "highlight": "bold cyan"
})

console = Console(theme=custom_theme)


class Logger:

    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)

    # --- Console Output ---

    def info(self, message: str):
        console.print(f"[info]ℹ  {message}[/info]")
        self._write(message, "INFO")

    def success(self, message: str):
        console.print(f"[success]✓  {message}[/success]")
        self._write(message, "SUCCESS")

    def warning(self, message: str):
        console.print(f"[warning]⚠  {message}[/warning]")
        self._write(message, "WARNING")

    def error(self, message: str):
        console.print(f"[error]✗  {message}[/error]")
        self._write(message, "ERROR")

    def highlight(self, message: str):
        console.print(f"[highlight]{message}[/highlight]")

    def line(self):
        console.print("─" * 40)

    def blank(self):
        console.print("")

    # --- File Write ---

    def _write(self, message: str, level: str):
        if not self.log_dir:
            return
        log_file = (
            self.log_dir /
            f"{datetime.now().strftime('%Y-%m-%d')}.log"
        )
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")


# --- Global logger instance ---
logger = Logger()