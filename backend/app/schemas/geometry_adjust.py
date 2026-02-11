"""Schemas for geometry adjustment (quick-adjust tools)."""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class AdjustPoint(BaseModel):
    """A 2D point."""

    x: float
    y: float


class GeometryAdjustRequest(BaseModel):
    """Request to adjust measurement geometry.

    The *action* field selects the operation and *params* carries
    action-specific arguments.
    """

    action: Literal["nudge", "snap_to_grid", "extend", "trim", "offset", "split", "join"]
    params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_params(self) -> "GeometryAdjustRequest":
        """Ensure required params are present for each action."""
        a = self.action
        p = self.params

        if a == "nudge" and "direction" not in p:
            raise ValueError("nudge requires 'direction' in params (up/down/left/right)")
        if a == "trim" and "trim_point" not in p:
            raise ValueError("trim requires 'trim_point' in params ({x, y})")
        if a == "split" and "split_point" not in p:
            raise ValueError("split requires 'split_point' in params ({x, y})")
        if a == "join" and "other_measurement_id" not in p:
            raise ValueError("join requires 'other_measurement_id' in params")

        return self


class GeometryAdjustResponse(BaseModel):
    """Response after a geometry adjustment."""

    status: str = "success"
    action: str
    measurement_id: str
    new_geometry_type: str
    new_geometry_data: dict[str, Any]
    new_quantity: float
    new_unit: str
    created_measurement_id: str | None = None  # For split action
