"""
Logging system for AgentARC with support for any Python logging package
"""

from enum import Enum
from typing import Optional
import logging
import sys


class LogLevel(Enum):
    """Log verbosity levels"""
    MINIMAL = "minimal"  # Only critical policy decisions
    INFO = "info"        # Standard operational info
    DEBUG = "debug"      # Detailed debugging info


class PolicyLogger:
    """Logger for policy enforcement with configurable verbosity

    This logger can work with any Python logging package by accepting
    a logger instance. If no logger is provided, it creates a default
    console logger.

    Args:
        level: LogLevel for filtering messages (MINIMAL, INFO, DEBUG)
        logger: Optional logging.Logger instance (or any compatible logger)
        use_emojis: Whether to include emoji prefixes (default: True)
        name: Logger name (default: "agentarc")

    Examples:
        # Use default console logger with emojis
        logger = PolicyLogger(level=LogLevel.INFO)

        # Use standard Python logging module
        import logging
        python_logger = logging.getLogger("my_app")
        logger = PolicyLogger(logger=python_logger)

        # Use loguru or any other logging package
        from loguru import logger as loguru_logger
        logger = PolicyLogger(logger=loguru_logger, use_emojis=False)
    """

    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        logger: Optional[logging.Logger] = None,
        use_emojis: bool = True,
        name: str = "agentarc"
    ):
        self.level = level
        self.use_emojis = use_emojis
        self._level_priority = {
            LogLevel.MINIMAL: 0,
            LogLevel.INFO: 1,
            LogLevel.DEBUG: 2
        }

        # Use provided logger or create a default one
        if logger is None:
            self._logger = self._create_default_logger(name)
            self._is_default_logger = True
        else:
            self._logger = logger
            self._is_default_logger = False

    def _create_default_logger(self, name: str) -> logging.Logger:
        """Create a default console logger with formatting"""
        logger = logging.getLogger(name)

        # Only configure if no handlers exist (avoid duplicate handlers)
        if not logger.handlers:
            logger.setLevel(logging.DEBUG)

            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)

            # Simple format without timestamps for cleaner output
            formatter = logging.Formatter('%(message)s')
            console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)
            logger.propagate = False

        return logger

    def _should_log(self, target_level: LogLevel) -> bool:
        """Check if message should be logged based on current level"""
        return self._level_priority[self.level] >= self._level_priority[target_level]

    def _format_message(self, message: str, emoji: str = "") -> str:
        """Format message with optional emoji prefix"""
        if self.use_emojis and emoji:
            return f"{emoji} {message}"
        return message

    def minimal(self, message: str):
        """Log critical policy decisions (always shown unless silent)"""
        if self._should_log(LogLevel.MINIMAL):
            formatted = self._format_message(message, "🛡️")
            self._logger.info(formatted)

    def info(self, message: str, prefix: str = "ℹ️"):
        """Log standard operational information"""
        if self._should_log(LogLevel.INFO):
            emoji = prefix if self.use_emojis else ""
            formatted = self._format_message(message, emoji.strip())
            self._logger.info(formatted)

    def debug(self, message: str):
        """Log detailed debugging information"""
        if self._should_log(LogLevel.DEBUG):
            if self.use_emojis:
                formatted = f"🔍 [DEBUG] {message}"
            else:
                formatted = f"[DEBUG] {message}"
            self._logger.debug(formatted)

    def success(self, message: str):
        """Log success messages"""
        if self._should_log(LogLevel.INFO):
            formatted = self._format_message(message, "✅")
            self._logger.info(formatted)

    def warning(self, message: str):
        """Log warnings"""
        if self._should_log(LogLevel.MINIMAL):
            formatted = self._format_message(message, "⚠️")
            self._logger.warning(formatted)

    def error(self, message: str):
        """Log errors (always shown)"""
        formatted = self._format_message(message, "❌")
        self._logger.error(formatted)

    def section(self, title: str):
        """Log section headers"""
        if self._should_log(LogLevel.INFO):
            separator = "=" * 60
            if self.use_emojis:
                header = f"\n{separator}\n🔍 {title}\n{separator}\n"
            else:
                header = f"\n{separator}\n{title}\n{separator}\n"
            self._logger.info(header)

    def subsection(self, title: str):
        """Log subsection headers"""
        if self._should_log(LogLevel.INFO):
            separator = "-" * 40
            formatted = f"\n{title}\n{separator}"
            self._logger.info(formatted)
