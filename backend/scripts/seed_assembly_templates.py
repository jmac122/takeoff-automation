"""Seed script to populate assembly templates.

Usage:
    cd backend && python -m scripts.seed_assembly_templates
"""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.data.assembly_templates import CONCRETE_ASSEMBLY_TEMPLATES
from app.models.assembly import AssemblyTemplate


async def seed_templates() -> None:
    """Insert concrete assembly templates (idempotent — skips existing names)."""
    settings = get_settings()
    engine = create_async_engine(str(settings.database_url))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        for tmpl_data in CONCRETE_ASSEMBLY_TEMPLATES:
            # Check if template already exists by name
            result = await session.execute(
                select(AssemblyTemplate).where(
                    AssemblyTemplate.name == tmpl_data["name"]
                )
            )
            if result.scalar_one_or_none() is not None:
                print(f"  SKIP (exists): {tmpl_data['name']}")
                continue

            template = AssemblyTemplate(
                id=uuid.uuid4(),
                name=tmpl_data["name"],
                description=tmpl_data.get("description"),
                scope=tmpl_data.get("scope", "concrete"),
                category=tmpl_data.get("category"),
                subcategory=tmpl_data.get("subcategory"),
                csi_code=tmpl_data.get("csi_code"),
                csi_description=tmpl_data.get("csi_description"),
                measurement_type=tmpl_data.get("measurement_type", "area"),
                expected_unit=tmpl_data.get("expected_unit", "SF"),
                default_waste_percent=tmpl_data.get("default_waste_percent", 5.0),
                productivity_rate=tmpl_data.get("productivity_rate"),
                productivity_unit=tmpl_data.get("productivity_unit"),
                crew_size=tmpl_data.get("crew_size"),
                is_system=True,
                is_active=True,
                version=1,
                component_definitions=tmpl_data.get("component_definitions", []),
            )
            session.add(template)
            print(f"  ADD: {tmpl_data['name']}")

        await session.commit()

    await engine.dispose()
    print("\nDone seeding assembly templates.")


if __name__ == "__main__":
    asyncio.run(seed_templates())
