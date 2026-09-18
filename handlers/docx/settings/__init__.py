"""Settings domain handlers: settings, compatibility, theme."""

from handlers.docx.settings.settings import SettingsHandler
from handlers.docx.settings.compatibility import CompatibilityHandler
from handlers.docx.settings.theme import ThemeHandler

__all__ = [
    "SettingsHandler",
    "CompatibilityHandler",
    "ThemeHandler",
]
