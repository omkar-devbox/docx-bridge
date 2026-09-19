from typing import Any
import xml.etree.ElementTree as ET

from config import (
    RELATIONSHIP_TYPES,
    INTERNAL_PLUMBING_TARGETS,
)
from handlers.docx.base import BaseHandler, qn, NAMESPACES


# --------------------------------
# Relationship Type Mappings
# --------------------------------

REL_TYPE_MAP = RELATIONSHIP_TYPES

URI_TO_SHORT_TYPE = {
    uri: short_type
    for short_type, uri in REL_TYPE_MAP.items()
}


# --------------------------------
# Relationships Handler
# --------------------------------

class RelationshipsHandler(BaseHandler):

    REL_NS = NAMESPACES.get(
        "rel",
        "",
    )

    def __init__(self, relationships_config: dict[str, Any] | None = None):
        self.relationships_config = relationships_config or {}
        self.rel_types = self.relationships_config.get("types") or RELATIONSHIP_TYPES
        self.uri_to_short_type = {
            uri: short_type
            for short_type, uri in self.rel_types.items()
        }
        self.internal_plumbing_targets = set(
            self.relationships_config.get("internal_plumbing_targets") or INTERNAL_PLUMBING_TARGETS
        )

    # --------------------------------
    # Relationship Type Helper
    # --------------------------------

    def get_short_type(
        self,
        raw_type: str,
    ) -> str:
        if raw_type in self.uri_to_short_type:
            return self.uri_to_short_type[raw_type]

        if raw_type in URI_TO_SHORT_TYPE:
            return URI_TO_SHORT_TYPE[raw_type]

        if "/" in raw_type:
            return raw_type.rsplit("/", 1)[-1]

        return raw_type

    @staticmethod
    def _get_short_type(
        raw_type: str,
    ) -> str:

        if raw_type in URI_TO_SHORT_TYPE:
            return URI_TO_SHORT_TYPE[
                raw_type
            ]

        if "/" in raw_type:
            return raw_type.rsplit(
                "/",
                1,
            )[-1]

        return raw_type


    # --------------------------------
    # Simple Mode Filter
    # --------------------------------

    def is_internal_plumbing(
        self,
        target: str,
        short_type: str,
    ) -> bool:
        if target in self.internal_plumbing_targets:
            return True

        if target in INTERNAL_PLUMBING_TARGETS:
            return True

        if target.startswith("theme/"):
            return True

        return short_type in (
            "styles",
            "numbering",
            "theme",
            "settings",
            "webSettings",
            "fontTable",
        )

    @staticmethod
    def _is_internal_plumbing(
        target: str,
        short_type: str,
    ) -> bool:

        if target in INTERNAL_PLUMBING_TARGETS:
            return True

        if target.startswith(
            "theme/"
        ):
            return True

        return short_type in (
            "styles",
            "numbering",
            "theme",
            "settings",
            "webSettings",
            "fontTable",
        )


    # --------------------------------
    # XML → JSON
    # --------------------------------

    def to_json(
        self,
        element: ET.Element,
        simple: bool = False,
    ) -> list[dict[str, Any]]:

        relationships: list[
            dict[str, Any]
        ] = []

        relationship_tag = qn(
            "rel:Relationship"
        )

        for relationship in element.findall(
            relationship_tag
        ):

            raw_type = relationship.attrib.get(
                "Type",
                "",
            )

            target = relationship.attrib.get(
                "Target",
                "",
            )

            short_type = (
                self.get_short_type(raw_type)
                if hasattr(self, "get_short_type")
                else self._get_short_type(raw_type)
            )

            # Hide internal OpenXML plumbing in simple mode.
            is_plumbing = (
                self.is_internal_plumbing(target, short_type)
                if hasattr(self, "is_internal_plumbing")
                else self._is_internal_plumbing(target, short_type)
            )
            if simple and is_plumbing:
                continue

            entry: dict[str, Any] = {
                "id": relationship.attrib.get(
                    "Id",
                    "",
                ),
                "type": (
                    short_type
                    if simple
                    else raw_type
                ),
                "target": target,
            }

            target_mode = relationship.attrib.get(
                "TargetMode"
            )

            if target_mode:
                entry["targetMode"] = (
                    target_mode
                )

            relationships.append(
                entry
            )

        return relationships


    # --------------------------------
    # Relationship List Normalization
    # --------------------------------

    @staticmethod
    def _normalize_relationships(
        data: list[dict[str, Any]] | dict[str, Any],
    ) -> list[dict[str, Any]]:

        relationships: list[
            dict[str, Any]
        ] = []

        if isinstance(
            data,
            dict,
        ):

            raw_relationships = (
                data.get("relations")
                or data.get("relationships")
                or []
            )

            if isinstance(
                raw_relationships,
                dict,
            ):

                for relationship_id, value in (
                    raw_relationships.items()
                ):

                    if not isinstance(
                        value,
                        dict,
                    ):
                        continue

                    entry = dict(
                        value
                    )

                    entry.setdefault(
                        "id",
                        relationship_id,
                    )

                    relationships.append(
                        entry
                    )

            elif isinstance(
                raw_relationships,
                list,
            ):

                relationships = list(
                    raw_relationships
                )

        elif isinstance(
            data,
            list,
        ):

            relationships = list(
                data
            )

        return relationships


    # --------------------------------
    # Relationship ID Collection
    # --------------------------------

    @staticmethod
    def _collect_used_rids(
        relationships: list[
            dict[str, Any]
        ],
    ) -> set[int]:

        used_rids: set[int] = set()

        for relationship in relationships:

            relationship_id = str(
                relationship.get(
                    "id",
                    "",
                )
            )

            if (
                relationship_id.startswith(
                    "rId"
                )
                and relationship_id[3:].isdigit()
            ):
                used_rids.add(
                    int(
                        relationship_id[3:]
                    )
                )

        return used_rids


    # --------------------------------
    # Relationship Type Resolution
    # --------------------------------

    def resolve_relationship_type(
        self,
        relationship: dict[str, Any],
    ) -> str:

        relationship_type = relationship.get(
            "type",
            "image",
        )

        if hasattr(self, "rel_types") and relationship_type in self.rel_types:
            return self.rel_types[relationship_type]

        return REL_TYPE_MAP.get(
            relationship_type,
            relationship_type,
        )

    @staticmethod
    def _resolve_relationship_type(
        relationship: dict[str, Any],
    ) -> str:

        relationship_type = relationship.get(
            "type",
            "image",
        )

        return REL_TYPE_MAP.get(
            relationship_type,
            relationship_type,
        )


    # --------------------------------
    # Relationship XML
    # --------------------------------

    @staticmethod
    def _build_relationship(
        relationship: dict[str, Any],
        relationship_id: str,
        full_type: str,
    ) -> ET.Element:

        attributes = {
            "Id": relationship_id,
            "Type": full_type,
            "Target": str(
                relationship.get(
                    "target",
                    "",
                )
            ),
        }

        target_mode = relationship.get(
            "targetMode"
        )

        if target_mode:
            attributes["TargetMode"] = str(
                target_mode
            )

        return ET.Element(
            qn("rel:Relationship"),
            attributes,
        )


    # --------------------------------
    # JSON → XML
    # --------------------------------

    def to_xml(
        self,
        data: list[dict[str, Any]]
        | dict[str, Any],
    ) -> ET.Element:

        root = ET.Element(
            qn("rel:Relationships")
        )

        relationships = (
            self._normalize_relationships(
                data
            )
        )

        used_rids = (
            self._collect_used_rids(
                relationships
            )
        )

        next_rid_number = (
            max(
                used_rids,
                default=0,
            )
            + 1
        )

        for relationship in relationships:

            if not isinstance(
                relationship,
                dict,
            ):
                continue

            relationship_id = str(
                relationship.get(
                    "id",
                    "",
                )
            )

            # Generate a unique rId when missing.
            if not relationship_id:

                relationship_id = (
                    f"rId{next_rid_number}"
                )

                next_rid_number += 1

            full_type = (
                self.resolve_relationship_type(relationship)
                if hasattr(self, "resolve_relationship_type")
                else self._resolve_relationship_type(
                    relationship
                )
            )

            root.append(
                self._build_relationship(
                    relationship,
                    relationship_id,
                    full_type,
                )
            )

        return root