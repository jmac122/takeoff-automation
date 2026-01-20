"""Project routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.document import Document
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter()


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(db: Annotated[AsyncSession, Depends(get_db)]):
    """List all projects with document counts."""
    result = await db.execute(
        select(Project, func.count(Document.id).label("document_count"))
        .outerjoin(Document)
        .group_by(Project.id)
    )

    projects_with_counts = []
    for project, doc_count in result.all():
        project_dict = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "client_name": project.client_name,
            "project_address": None,  # Not in model yet
            "status": project.status,
            "document_count": doc_count,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
        projects_with_counts.append(project_dict)

    return projects_with_counts


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get a single project by ID."""
    result = await db.execute(
        select(Project, func.count(Document.id).label("document_count"))
        .outerjoin(Document)
        .where(Project.id == project_id)
        .group_by(Project.id)
    )

    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    project, doc_count = row
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "client_name": project.client_name,
        "project_address": None,
        "status": project.status,
        "document_count": doc_count,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


@router.get("/{project_id}/documents")
async def get_project_documents(
    project_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get all documents for a project."""
    # First verify project exists
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get documents
    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    return {"documents": documents}


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Create a new project."""
    project = Project(**project_data.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "client_name": project.client_name,
        "project_address": None,
        "status": project.status,
        "document_count": 0,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
