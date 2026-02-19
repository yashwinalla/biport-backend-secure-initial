import logging


def setup_logger(logger_name: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers if the logger was already configured
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler for logging to stdout
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:\
                %(lineno)d - %(message)s"
        )
    )
    logger.addHandler(console_handler)

    return logger


logger = setup_logger("BIport-Log")
