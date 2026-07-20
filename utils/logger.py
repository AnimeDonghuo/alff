# utils/logger.py
import logging
import sys

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RED = "\033[31m"

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        color = RESET
        if record.levelno == logging.INFO:
            color = GREEN
        elif record.levelno == logging.WARNING:
            color = YELLOW
        elif record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            color = RED
        elif record.levelno == logging.DEBUG:
            color = BLUE
            
        record.levelname = f"{color}{record.levelname}{RESET}"
        record.msg = f"{BOLD}{record.msg}{RESET}"
        return super().format(record)

logger = logging.getLogger("RSSBot")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(ColoredFormatter("[%(asctime)s] [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s"))
logger.addHandler(handler)
