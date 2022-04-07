import datetime
import logging
from logging import handlers
import platform
import re

def createLogger(name: str):
    """
    Create a logger with a rotating file handler
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = handlers.RotatingFileHandler(
        filename=f"{name}.log",
        maxBytes=1000000,
        backupCount=5
    )
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    #Print out the session info + any relevant OS info
    logger.info(
        "{_date}\r\n{system_info}\r\n{separator}".format(
            _date=datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y"),
            system_info="{0} {1} - build: {2}".format(
                platform.system(),
                platform.release(),
                platform.version()
            ),
            separator="=" * 50
        )
    )

    #The above doesn't need formatting, so we apply this after
    handler.setFormatter(LogFormatter())
    return logger

class LogFormatter(logging.Formatter):
    """
    log formatter all other mas logs should extend if they want
    custom functionality.

    Features:
        - uses our own log tags
        - defaults format with time and level name
    """
    # log tags
    LT_INFO = "info"
    LT_WARN = "WARNING"
    LT_ERROR = "!ERROR!"

    LT_MAP = {
        logging.INFO: LT_INFO,
        logging.WARN: LT_WARN,
        logging.ERROR: LT_ERROR,
    }

    #Consts
    DEF_FMT = "[%(asctime)s] [%(levelname)s]: %(message)s"
    DEF_DATEFMT = "%Y-%m-%d %H:%M:%S"

    NEWLINE_MATCHER = re.compile(r"(?<!\r)\n")
    LINE_TERMINATOR = "\r\n"

    def __init__(self, fmt=None, datefmt=None):
        if fmt is None:
            fmt = self.DEF_FMT
        if datefmt is None:
            datefmt = self.DEF_DATEFMT

        super().__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record):
        """
        Override of format - mainly replaces the levelname prop
        """
        self.update_levelname(record)
        return self.replace_lf(
            super().format(record)
        )

    def update_levelname(self, record):
        """
        Updates the levelname of the record. Use in custom formatter
        functions.
        """
        record.levelname = self.LT_MAP.get(record.levelno, record.levelname)

    @classmethod
    def replace_lf(cls, msg):
        """
        Replaces all line feeds with carriage returns and a line feed
        """
        return re.sub(cls.NEWLINE_MATCHER, cls.LINE_TERMINATOR, msg)
