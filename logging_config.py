import sys
import logging
from datetime import datetime


class TeeOutput:
    """Schrijft stdout tegelijk naar de console én naar een logbestand."""

    def __init__(self, console, logfile):
        self.console = console
        self.logfile = logfile

    def write(self, text):
        self.console.write(text)
        self.logfile.write(text)

    def flush(self):
        self.console.flush()
        self.logfile.flush()

    def isatty(self):
        return False


def setup_logging(log_path: str = "agent_log.txt") -> logging.Logger:
    """
    Zet logging op:
    - Alle stdout (inclusief LangChain verbose output) → agent_log.txt
    - Python logger → session.log + console
    """
    # Open logbestand voor LangChain verbose output
    log_file = open(log_path, "w", encoding="utf-8")
    log_file.write(f"=== Hotel Agent sessie gestart: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

    # Leid stdout om zodat LangChain verbose=True output ook in het bestand terechtkomt
    sys.stdout = TeeOutput(sys.__stdout__, log_file)

    # Python logger voor sessie-events
    logger = logging.getLogger("hotel_agent")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    # Handler: session.log
    file_handler = logging.FileHandler("session.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Handler: console (via de originele stdout)
    console_handler = logging.StreamHandler(sys.__stdout__)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger
