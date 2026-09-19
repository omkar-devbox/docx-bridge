import unittest
import xml.etree.ElementTree as ET

from config import (
    COMPATIBILITY_URI,
    CONTENT_TYPES_DEFAULTS,
    CONTENT_TYPES_NAMESPACE,
    CONTENT_TYPES_OVERRIDES,
    DEFAULT_ORIENTATION,
    DEFAULT_PAGE_HEIGHT,
    DEFAULT_PAGE_WIDTH,
    NAMESPACES,
)
from handlers.docx.advanced.charts import CHART_NS, ChartsHandler
from handlers.docx.advanced.math import MATH_NS, MathHandler
from handlers.docx.advanced.smartart import DGM_NS, SmartArtHandler
from handlers.docx.document.properties import (
    APP_NS,
    CORE_NS,
    DC_NS,
    DCTERMS_NS,
    PropertiesHandler,
    VT_NS,
    XSI_NS,
)
from handlers.docx.package.content_types import (
    CONTENT_TYPES_NS,
    DEFAULT_EXTENSIONS,
    DEFAULT_OVERRIDES,
    ContentTypesHandler,
)
from handlers.docx.sections.page import PageHandler
from handlers.docx.settings.compatibility import CompatibilityHandler
from handlers.docx.settings.settings import SettingsHandler
from handlers.docx.settings.theme import THEME_NS, ThemeHandler


class TestHandlersConfig(unittest.TestCase):

    def test_content_types_handler_references_config(self):
        """Test ContentTypesHandler uses config definitions."""
        self.assertEqual(CONTENT_TYPES_NS, CONTENT_TYPES_NAMESPACE)
        self.assertEqual(DEFAULT_EXTENSIONS, CONTENT_TYPES_DEFAULTS)
        self.assertEqual(DEFAULT_OVERRIDES, CONTENT_TYPES_OVERRIDES)

        handler = ContentTypesHandler()
        xml = handler.to_xml()
        self.assertEqual(xml.tag, f"{{{CONTENT_TYPES_NAMESPACE}}}Types")

    def test_properties_handler_namespaces_reference_config(self):
        """Test PropertiesHandler uses config namespaces."""
        self.assertEqual(CORE_NS, NAMESPACES.get("cp"))
        self.assertEqual(DC_NS, NAMESPACES.get("dc"))
        self.assertEqual(DCTERMS_NS, NAMESPACES.get("dcterms"))
        self.assertEqual(APP_NS, NAMESPACES.get("ep"))
        self.assertEqual(XSI_NS, NAMESPACES.get("xsi"))
        self.assertEqual(VT_NS, NAMESPACES.get("vt"))

    def test_advanced_handlers_namespaces_reference_config(self):
        """Test charts, smartart, math, and theme handlers use config namespaces."""
        self.assertEqual(CHART_NS, NAMESPACES.get("c"))
        self.assertEqual(DGM_NS, NAMESPACES.get("dgm"))
        self.assertEqual(MATH_NS, NAMESPACES.get("m"))
        self.assertEqual(THEME_NS, NAMESPACES.get("a"))

    def test_compatibility_handlers_reference_config(self):
        """Test compatibility and settings handlers use COMPATIBILITY_URI from config."""
        compat_handler = CompatibilityHandler()
        el = compat_handler.to_xml({"compatibilityMode": "15"})
        child = el.find(f".//{{{NAMESPACES.get('w')}}}compatSetting")
        self.assertIsNotNone(child)
        self.assertEqual(child.attrib.get(f"{{{NAMESPACES.get('w')}}}uri"), COMPATIBILITY_URI)

        settings_handler = SettingsHandler()
        s_el = settings_handler.to_xml({})
        s_child = s_el.find(f".//{{{NAMESPACES.get('w')}}}compatSetting")
        self.assertIsNotNone(s_child)
        self.assertEqual(s_child.attrib.get(f"{{{NAMESPACES.get('w')}}}uri"), COMPATIBILITY_URI)

    def test_page_handler_references_config_defaults(self):
        """Test page handler generates page sizes using config defaults."""
        page_handler = PageHandler()
        el = page_handler.to_xml({"size": {}})
        pg_sz = el.find(f"{{{NAMESPACES.get('w')}}}pgSz")
        self.assertIsNotNone(pg_sz)
        self.assertEqual(pg_sz.attrib.get(f"{{{NAMESPACES.get('w')}}}w"), str(DEFAULT_PAGE_WIDTH))
        self.assertEqual(pg_sz.attrib.get(f"{{{NAMESPACES.get('w')}}}h"), str(DEFAULT_PAGE_HEIGHT))


if __name__ == "__main__":
    unittest.main()
