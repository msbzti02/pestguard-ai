"""
Structured Logger — core/logger.py
====================================
Provides a consistent, timestamped logger for all backend modules.

Features:
    - Console + rotating file output
    - Colour-coded log levels in console (INFO=green, WARNING=yellow, ERROR=red)
    - Single call: get_logger(__name__)
    - Log file: logs/pestguard.log (auto-created, 5MB × 3 backups)
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


# ── ANSI colour codes for console output ─────────────────────────────────────
class _ColourFormatter(logging.Formatter):
    COLOURS = {
        logging.DEBUG:    "\033[37m",    # White
        logging.INFO:     "\033[32m",    # Green
        logging.WARNING:  "\033[33m",    # Yellow
        logging.ERROR:    "\033[31m",    # Red
        logging.CRITICAL: "\033[35m",    # Magenta
    }
    RESET = "\033[0m"
    FMT = "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s"

    def format(self, record: logging.LogRecord) -> str:
        colour = self.COLOURS.get(record.levelno, "")
        formatter = logging.Formatter(f"{colour}{self.FMT}{self.RESET}", datefmt="%H:%M:%S")
        return formatter.format(record)


# ── File formatter (no colour codes) ─────────────────────────────────────────
_FILE_FMT = logging.Formatter(
    "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a named logger with console + rotating-file handlers.

    Usage:
        from core.logger import get_logger
        log = get_logger(__name__)
        log.info("Server started")
        log.warning("VLM not ready — using mock")
        log.error("Weather API failed", exc_info=True)
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(_ColourFormatter())
    logger.addHandler(ch)

    # File handler — logs/pestguard.log (5MB × 3 backups)
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    fh = RotatingFileHandler(
        log_dir / "pestguard.log",
        maxBytes=5 * 1024 * 1024,   # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_FILE_FMT)
    logger.addHandler(fh)

    # Don't propagate to root logger (avoids double printing)
    logger.propagate = False

    return logger
