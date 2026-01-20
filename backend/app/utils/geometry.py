"""Geometry calculation utilities."""

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class Point:
    """2D point."""
    x: float
    y: float
    
    def distance_to(self, other: "Point") -> float:
        """Calculate distance to another point."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "Point":
        return cls(x=data["x"], y=data["y"])


def calculate_line_length(start: Point, end: Point) -> float:
    """Calculate length of a line segment."""
    return start.distance_to(end)


def calculate_polyline_length(points: list[Point]) -> float:
    """Calculate total length of a polyline."""
    if len(points) < 2:
        return 0.0
    
    total = 0.0
    for i in range(len(points) - 1):
        total += points[i].distance_to(points[i + 1])
    
    return total


def calculate_polygon_area(points: list[Point]) -> float:
    """Calculate area of a polygon using the shoelace formula."""
    if len(points) < 3:
        return 0.0
    
    n = len(points)
    area = 0.0
    
    for i in range(n):
        j = (i + 1) % n
        area += points[i].x * points[j].y
        area -= points[j].x * points[i].y
    
    return abs(area) / 2.0


def calculate_polygon_perimeter(points: list[Point]) -> float:
    """Calculate perimeter of a polygon."""
    if len(points) < 2:
        return 0.0
    
    perimeter = calculate_polyline_length(points)
    # Close the polygon
    perimeter += points[-1].distance_to(points[0])
    
    return perimeter


def calculate_rectangle_area(width: float, height: float) -> float:
    """Calculate area of a rectangle."""
    return width * height


def calculate_rectangle_perimeter(width: float, height: float) -> float:
    """Calculate perimeter of a rectangle."""
    return 2 * (width + height)


def calculate_circle_area(radius: float) -> float:
    """Calculate area of a circle."""
    return math.pi * radius ** 2


def calculate_circle_circumference(radius: float) -> float:
    """Calculate circumference of a circle."""
    return 2 * math.pi * radius


class MeasurementCalculator:
    """Calculator for converting measurements to real-world units."""
    
    def __init__(self, pixels_per_foot: float):
        """
        Args:
            pixels_per_foot: Scale factor (pixels per real foot)
        """
        self.pixels_per_foot = pixels_per_foot
    
    def pixels_to_feet(self, pixels: float) -> float:
        """Convert pixel distance to feet."""
        return pixels / self.pixels_per_foot
    
    def pixels_to_square_feet(self, pixel_area: float) -> float:
        """Convert pixel area to square feet."""
        return pixel_area / (self.pixels_per_foot ** 2)
    
    def square_feet_to_cubic_yards(
        self,
        square_feet: float,
        depth_inches: float,
    ) -> float:
        """Convert square feet to cubic yards given depth.
        
        Args:
            square_feet: Area in square feet
            depth_inches: Depth/thickness in inches
            
        Returns:
            Volume in cubic yards
        """
        depth_feet = depth_inches / 12
        cubic_feet = square_feet * depth_feet
        cubic_yards = cubic_feet / 27
        return cubic_yards
    
    def calculate_line(
        self,
        start: dict[str, float],
        end: dict[str, float],
    ) -> dict[str, float]:
        """Calculate line measurement.
        
        Returns:
            Dict with pixel_length and length_feet
        """
        p1 = Point.from_dict(start)
        p2 = Point.from_dict(end)
        
        pixel_length = calculate_line_length(p1, p2)
        length_feet = self.pixels_to_feet(pixel_length)
        
        return {
            "pixel_length": pixel_length,
            "length_feet": length_feet,
        }
    
    def calculate_polyline(
        self,
        points: list[dict[str, float]],
    ) -> dict[str, float]:
        """Calculate polyline measurement.
        
        Returns:
            Dict with pixel_length, length_feet, and segment_lengths
        """
        pts = [Point.from_dict(p) for p in points]
        
        pixel_length = calculate_polyline_length(pts)
        length_feet = self.pixels_to_feet(pixel_length)
        
        # Calculate individual segments
        segment_lengths = []
        for i in range(len(pts) - 1):
            seg_pixels = pts[i].distance_to(pts[i + 1])
            segment_lengths.append({
                "pixel_length": seg_pixels,
                "length_feet": self.pixels_to_feet(seg_pixels),
            })
        
        return {
            "pixel_length": pixel_length,
            "length_feet": length_feet,
            "segment_count": len(segment_lengths),
            "segment_lengths": segment_lengths,
        }
    
    def calculate_polygon(
        self,
        points: list[dict[str, float]],
        depth_inches: float | None = None,
    ) -> dict[str, float]:
        """Calculate polygon measurement.
        
        Returns:
            Dict with area, perimeter, and optionally volume
        """
        pts = [Point.from_dict(p) for p in points]
        
        pixel_area = calculate_polygon_area(pts)
        pixel_perimeter = calculate_polygon_perimeter(pts)
        
        area_sf = self.pixels_to_square_feet(pixel_area)
        perimeter_lf = self.pixels_to_feet(pixel_perimeter)
        
        result = {
            "pixel_area": pixel_area,
            "pixel_perimeter": pixel_perimeter,
            "area_sf": area_sf,
            "perimeter_lf": perimeter_lf,
        }
        
        if depth_inches:
            result["volume_cy"] = self.square_feet_to_cubic_yards(
                area_sf, depth_inches
            )
            result["depth_inches"] = depth_inches
        
        return result
    
    def calculate_rectangle(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        depth_inches: float | None = None,
    ) -> dict[str, float]:
        """Calculate rectangle measurement.
        
        Returns:
            Dict with dimensions, area, perimeter, and optionally volume
        """
        pixel_area = calculate_rectangle_area(width, height)
        pixel_perimeter = calculate_rectangle_perimeter(width, height)
        
        width_feet = self.pixels_to_feet(width)
        height_feet = self.pixels_to_feet(height)
        area_sf = self.pixels_to_square_feet(pixel_area)
        perimeter_lf = self.pixels_to_feet(pixel_perimeter)
        
        result = {
            "pixel_width": width,
            "pixel_height": height,
            "pixel_area": pixel_area,
            "pixel_perimeter": pixel_perimeter,
            "width_feet": width_feet,
            "height_feet": height_feet,
            "area_sf": area_sf,
            "perimeter_lf": perimeter_lf,
        }
        
        if depth_inches:
            result["volume_cy"] = self.square_feet_to_cubic_yards(
                area_sf, depth_inches
            )
            result["depth_inches"] = depth_inches
        
        return result
    
    def calculate_circle(
        self,
        center: dict[str, float],
        radius: float,
        depth_inches: float | None = None,
    ) -> dict[str, float]:
        """Calculate circle measurement.
        
        Returns:
            Dict with radius, diameter, area, circumference, and optionally volume
        """
        pixel_area = calculate_circle_area(radius)
        pixel_circumference = calculate_circle_circumference(radius)
        
        radius_feet = self.pixels_to_feet(radius)
        diameter_feet = radius_feet * 2
        area_sf = self.pixels_to_square_feet(pixel_area)
        circumference_lf = self.pixels_to_feet(pixel_circumference)
        
        result = {
            "pixel_radius": radius,
            "pixel_area": pixel_area,
            "pixel_circumference": pixel_circumference,
            "radius_feet": radius_feet,
            "diameter_feet": diameter_feet,
            "area_sf": area_sf,
            "circumference_lf": circumference_lf,
        }
        
        if depth_inches:
            result["volume_cy"] = self.square_feet_to_cubic_yards(
                area_sf, depth_inches
            )
            result["depth_inches"] = depth_inches
        
        return result
    
    def calculate_count(self, x: float, y: float) -> dict[str, Any]:
        """Calculate count measurement (just returns 1).
        
        Returns:
            Dict with count and position
        """
        return {
            "count": 1,
            "position": {"x": x, "y": y},
        }
