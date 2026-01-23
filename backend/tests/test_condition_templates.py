from app.api.routes.conditions import CONDITION_TEMPLATES
from app.schemas.condition import ConditionTemplateResponse


def test_condition_templates_include_required_names() -> None:
    names = {template["name"] for template in CONDITION_TEMPLATES}
    expected = {
        "Strip Footing",
        "Spread Footing",
        "Foundation Wall",
        "Grade Beam",
        '4" SOG',
        '6" SOG Reinforced',
        '4" Sidewalk',
        '6" Concrete Paving',
        "Curb & Gutter",
        "Concrete Column",
        '8" Concrete Wall',
        "Concrete Pier",
        "Catch Basin",
    }

    assert expected.issubset(names)


def test_templates_include_default_styling() -> None:
    for template in CONDITION_TEMPLATES:
        assert template["line_width"] == 2
        assert template["fill_opacity"] == 0.3


def test_template_response_defaults_apply() -> None:
    template = ConditionTemplateResponse.model_validate(
        {
            "name": "Custom Template",
            "scope": "concrete",
            "category": "misc",
            "measurement_type": "area",
            "unit": "SF",
            "color": "#90A4AE",
        }
    )

    assert template.line_width == 2
    assert template.fill_opacity == 0.3
