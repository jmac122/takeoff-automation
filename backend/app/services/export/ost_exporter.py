"""On Screen Takeoff (OST) XML exporter."""

from io import BytesIO
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from xml.dom import minidom

from app.services.export.base import BaseExporter, ExportData


class OSTExporter(BaseExporter):
    """Export project data to OST-compatible XML format."""

    @property
    def content_type(self) -> str:
        return "application/xml"

    @property
    def file_extension(self) -> str:
        return ".xml"

    def generate(self, data: ExportData, options: dict | None = None) -> bytes:
        root = Element("OSTProject")
        root.set("version", "1.0")
        root.set("name", data.project_name)

        # Project info
        project_el = SubElement(root, "ProjectInfo")
        SubElement(project_el, "Name").text = data.project_name
        if data.project_description:
            SubElement(project_el, "Description").text = data.project_description
        if data.client_name:
            SubElement(project_el, "Client").text = data.client_name

        # Conditions
        conditions_el = SubElement(root, "Conditions")
        for cond in data.conditions:
            cond_el = SubElement(conditions_el, "Condition")
            cond_el.set("id", str(cond.id))
            SubElement(cond_el, "Name").text = cond.name
            SubElement(cond_el, "Type").text = cond.measurement_type
            SubElement(cond_el, "Unit").text = cond.unit
            SubElement(cond_el, "Color").text = cond.color
            if cond.description:
                SubElement(cond_el, "Description").text = cond.description
            SubElement(cond_el, "TotalQuantity").text = f"{cond.total_quantity:.4f}"

            # Takeoff items (measurements)
            items_el = SubElement(cond_el, "TakeoffItems")
            for m in cond.measurements:
                item_el = SubElement(items_el, "TakeoffItem")
                item_el.set("id", str(m.id))
                SubElement(item_el, "PageNumber").text = str(m.page_number)
                if m.sheet_number:
                    SubElement(item_el, "SheetNumber").text = m.sheet_number
                SubElement(item_el, "GeometryType").text = m.geometry_type
                SubElement(item_el, "Quantity").text = f"{m.quantity:.4f}"
                SubElement(item_el, "Unit").text = m.unit

                # Geometry coordinates
                geom_el = SubElement(item_el, "Geometry")
                self._write_geometry(geom_el, m.geometry_type, m.geometry_data)

        # Pretty-print XML
        rough_string = tostring(root, encoding="unicode")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding="utf-8")

    @staticmethod
    def _write_geometry(parent: Element, geom_type: str, geom_data: dict) -> None:
        """Write geometry coordinates to XML element."""
        if geom_type in ("line",):
            start = geom_data.get("start", {})
            end = geom_data.get("end", {})
            start_el = SubElement(parent, "Start")
            SubElement(start_el, "X").text = str(start.get("x", 0))
            SubElement(start_el, "Y").text = str(start.get("y", 0))
            end_el = SubElement(parent, "End")
            SubElement(end_el, "X").text = str(end.get("x", 0))
            SubElement(end_el, "Y").text = str(end.get("y", 0))

        elif geom_type in ("polyline", "polygon"):
            points = geom_data.get("points", [])
            points_el = SubElement(parent, "Points")
            for pt in points:
                pt_el = SubElement(points_el, "Point")
                SubElement(pt_el, "X").text = str(pt.get("x", 0))
                SubElement(pt_el, "Y").text = str(pt.get("y", 0))

        elif geom_type == "rectangle":
            SubElement(parent, "X").text = str(geom_data.get("x", 0))
            SubElement(parent, "Y").text = str(geom_data.get("y", 0))
            SubElement(parent, "Width").text = str(geom_data.get("width", 0))
            SubElement(parent, "Height").text = str(geom_data.get("height", 0))
            if "rotation" in geom_data:
                SubElement(parent, "Rotation").text = str(geom_data["rotation"])

        elif geom_type == "circle":
            center = geom_data.get("center", {})
            SubElement(parent, "CenterX").text = str(center.get("x", 0))
            SubElement(parent, "CenterY").text = str(center.get("y", 0))
            SubElement(parent, "Radius").text = str(geom_data.get("radius", 0))

        elif geom_type == "point":
            SubElement(parent, "X").text = str(geom_data.get("x", 0))
            SubElement(parent, "Y").text = str(geom_data.get("y", 0))
