"""Numbering and list item detection and provisioning helpers for DOCX packages."""

from typing import Any
from handlers.docx.numbering import NumberingHandler


def extract_all_items(
    data: dict[str, Any] | list[Any],
) -> list[Any]:
    """Extract all item nodes from document sections, body, or content."""
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    items: list[Any] = []

    # Section-based document
    sections = data.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue

            content = section.get(
                "content",
                section.get("children", []),
            )

            if isinstance(content, list):
                items.extend(content)

        return items

    # Body-based document
    body = data.get("body")

    if isinstance(body, dict):
        content = body.get("content", [])

        if isinstance(content, list):
            items.extend(content)

    elif isinstance(body, list):
        items.extend(body)

    # Direct content
    elif isinstance(data.get("content"), list):
        items.extend(data["content"])

    return items


def has_list_or_numbering(
    data: dict[str, Any],
) -> bool:
    """Check whether document items contain any list or bullet items."""
    all_items = extract_all_items(data)

    if not all_items:
        return False

    def check_item(item: Any) -> bool:
        if not isinstance(item, dict):
            return False

        item_type = item.get("type")

        if item_type in (
            "bullet",
            "list_item",
            "listItem",
            "list",
        ):
            return True

        if any(
            item.get(key)
            for key in (
                "bullet",
                "list",
                "numbering",
                "numbered",
                "number",
            )
        ):
            return True

        if isinstance(item.get("items"), list):
            return True

        rows = item.get("rows")

        if isinstance(rows, list):
            for row in rows:

                # Row represented as a list
                if isinstance(row, list):
                    for cell in row:
                        if check_item(cell):
                            return True

                        if (
                            isinstance(cell, dict)
                            and isinstance(cell.get("content"), list)
                        ):
                            for sub_item in cell["content"]:
                                if check_item(sub_item):
                                    return True

                # Row represented as a dictionary
                elif isinstance(row, dict):
                    cells = row.get("cells")

                    if isinstance(cells, list):
                        for cell in cells:
                            if check_item(cell):
                                return True

        return False

    for item in all_items:
        if check_item(item):
            return True

    return False


def ensure_numbering(
    data: dict[str, Any],
) -> None:
    """Ensure numbering definitions and IDs exist for all list/bullet items in data."""
    if not has_list_or_numbering(data):
        return

    # Create default numbering when missing
    if "numbering" not in data or not data["numbering"]:
        data["numbering"] = (
            NumberingHandler.build_default_numbering()
        )

    elif (
        isinstance(data["numbering"], dict)
        and not data["numbering"].get("abstractNumbering")
    ):
        data["numbering"] = (
            NumberingHandler.build_default_numbering()
        )

    num_dict = data["numbering"]

    if not isinstance(num_dict, dict):
        return

    abstract_list = num_dict.setdefault(
        "abstractNumbering",
        [],
    )

    instance_list = num_dict.setdefault(
        "numbering",
        [],
    )

    used_abs_ids = {
        int(item["id"])
        for item in abstract_list
        if isinstance(item, dict)
        and str(item.get("id", "")).isdigit()
    }

    used_num_ids = {
        int(item["numId"])
        for item in instance_list
        if isinstance(item, dict)
        and str(item.get("numId", "")).isdigit()
    }

    symbol_to_num_id: dict[str, int] = {}

    def process_item(item: Any) -> None:
        if not isinstance(item, dict):
            return

        # Detect custom bullet/list symbol
        raw_symbol = None

        if (
            "bullet" in item
            and item["bullet"] not in (False, None)
        ):
            bullet_value = item["bullet"]

            if isinstance(bullet_value, dict):
                raw_symbol = (
                    bullet_value.get("icon")
                    or bullet_value.get("style")
                    or bullet_value.get("type")
                    or bullet_value.get("format")
                )

            elif not isinstance(bullet_value, bool):
                raw_symbol = str(bullet_value)

        elif (
            "list" in item
            and item["list"] not in (False, None)
        ):
            list_value = item["list"]

            if isinstance(list_value, dict):
                raw_symbol = (
                    list_value.get("icon")
                    or list_value.get("style")
                    or list_value.get("type")
                    or list_value.get("format")
                )

            elif not isinstance(list_value, bool):
                raw_symbol = str(list_value)

        if raw_symbol:
            known_id = NumberingHandler.get_known_preset_id(
                raw_symbol
            )

            # Register custom bullet symbol
            if known_id is None:
                if raw_symbol not in symbol_to_num_id:
                    next_id = (
                        max(
                            used_num_ids | used_abs_ids,
                            default=0,
                        )
                        + 1
                    )

                    used_abs_ids.add(next_id)
                    used_num_ids.add(next_id)

                    abstract_list.append(
                        NumberingHandler.build_custom_bullet_abstract_num(
                            raw_symbol,
                            next_id,
                        )
                    )

                    instance_list.append(
                        {
                            "numId": str(next_id),
                            "abstractNumId": str(next_id),
                        }
                    )

                    symbol_to_num_id[raw_symbol] = next_id

                custom_id = symbol_to_num_id[raw_symbol]
                level = item.get("level", 0)

                item["numbering"] = {
                    "id": custom_id,
                    "level": level,
                }

        # Process table rows/cells recursively
        rows = item.get("rows")

        if not isinstance(rows, list):
            return

        for row in rows:

            # Row as list
            if isinstance(row, list):
                for cell in row:
                    process_item(cell)

                    if (
                        isinstance(cell, dict)
                        and isinstance(cell.get("content"), list)
                    ):
                        for sub_item in cell["content"]:
                            process_item(sub_item)

            # Row as dictionary
            elif isinstance(row, dict):
                cells = row.get("cells")

                if not isinstance(cells, list):
                    continue

                for cell in cells:
                    process_item(cell)

                    if (
                        isinstance(cell, dict)
                        and isinstance(cell.get("content"), list)
                    ):
                        for sub_item in cell["content"]:
                            process_item(sub_item)

    for item in extract_all_items(data):
        process_item(item)
