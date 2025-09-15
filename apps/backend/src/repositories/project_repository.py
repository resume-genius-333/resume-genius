"""Repository for project-related database operations."""

from typing import Optional, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from src.models.db.project import (
    Project,
    ProjectSchema,
    ProjectTask,
    ProjectTaskSchema,
)
from src.models.llm.project import ProjectLLMSchema, ProjectTaskLLMSchema


class ProjectRepository:
    """Repository for project database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize project repository with database session."""
        self.session = session

    # Project methods
    async def create_project(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        llm_schema: ProjectLLMSchema,
    ) -> ProjectSchema:
        """Create a new project record in the database."""
        project = Project.from_llm(
            user_id=user_id,
            project_id=project_id,
            llm_schema=llm_schema,
        )

        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)

        return project.schema

    async def get_project_by_id(
        self, project_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ProjectSchema]:
        """Get a project record by ID, optionally filtered by user."""
        query = select(Project).where(Project.id == project_id)

        if user_id:
            query = query.where(Project.user_id == user_id)

        result = await self.session.execute(query)
        project = result.scalar_one_or_none()
        return project.schema if project else None

    async def get_projects_by_user(
        self,
        user_id: uuid.UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ProjectSchema]:
        """Get all project records for a specific user."""
        query = select(Project).where(Project.user_id == user_id)

        # Order by end_date descending (most recent first), with NULL values first (ongoing projects)
        query = query.order_by(Project.end_date.desc().nullsfirst())

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        result = await self.session.execute(query)
        projects = list(result.scalars().all())
        return [project.schema for project in projects]

    async def get_projects_count(
        self,
        user_id: uuid.UUID,
    ) -> int:
        """Get the count of project records for a user."""
        query = select(func.count()).select_from(Project).where(Project.user_id == user_id)
        result = await self.session.scalar(query)
        return result or 0

    async def update_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ProjectSchema]:
        """Update project fields."""
        query = select(Project).where(Project.id == project_id).where(Project.user_id == user_id)
        result = await self.session.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            return None

        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)

        await self.session.commit()
        await self.session.refresh(project)

        return project.schema

    async def delete_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a project record and all related tasks."""
        query = select(Project).where(Project.id == project_id).where(Project.user_id == user_id)
        result = await self.session.execute(query)
        project = result.scalar_one_or_none()

        if not project:
            return False

        await self.session.delete(project)
        await self.session.commit()

        return True

    # ProjectTask methods
    async def create_task(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        llm_schema: ProjectTaskLLMSchema,
    ) -> ProjectTaskSchema:
        """Create a new project task record."""
        task = ProjectTask.from_llm(
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            llm_schema=llm_schema,
        )

        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)

        return task.schema

    async def get_task_by_id(
        self, task_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ProjectTaskSchema]:
        """Get a project task by ID."""
        query = select(ProjectTask).where(ProjectTask.id == task_id)

        if user_id:
            query = query.where(ProjectTask.user_id == user_id)

        result = await self.session.execute(query)
        task = result.scalar_one_or_none()
        return task.schema if task else None

    async def get_tasks_by_project(
        self,
        project_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> List[ProjectTaskSchema]:
        """Get all tasks for a specific project."""
        query = select(ProjectTask).where(ProjectTask.project_id == project_id)

        if user_id:
            query = query.where(ProjectTask.user_id == user_id)

        result = await self.session.execute(query)
        tasks = list(result.scalars().all())
        return [task.schema for task in tasks]

    async def update_task(
        self, task_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> Optional[ProjectTaskSchema]:
        """Update task fields."""
        query = (
            select(ProjectTask)
            .where(ProjectTask.id == task_id)
            .where(ProjectTask.user_id == user_id)
        )
        result = await self.session.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            return None

        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        await self.session.commit()
        await self.session.refresh(task)

        return task.schema

    async def delete_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a task record."""
        query = (
            select(ProjectTask)
            .where(ProjectTask.id == task_id)
            .where(ProjectTask.user_id == user_id)
        )
        result = await self.session.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            return False

        await self.session.delete(task)
        await self.session.commit()

        return True

    async def bulk_create_tasks(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        tasks_data: List[tuple[uuid.UUID, ProjectTaskLLMSchema]],
    ) -> List[ProjectTaskSchema]:
        """Bulk create multiple task records for a project."""
        tasks = []
        for task_id, llm_schema in tasks_data:
            task = ProjectTask.from_llm(
                user_id=user_id,
                project_id=project_id,
                task_id=task_id,
                llm_schema=llm_schema,
            )
            tasks.append(task)
            self.session.add(task)

        await self.session.commit()

        # Refresh all tasks
        for task in tasks:
            await self.session.refresh(task)

        return [task.schema for task in tasks]

    async def delete_tasks_by_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> int:
        """Delete all tasks for a specific project."""
        stmt = delete(ProjectTask).where(
            ProjectTask.project_id == project_id,
            ProjectTask.user_id == user_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def get_project_with_tasks(
        self, project_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[tuple[ProjectSchema, List[ProjectTaskSchema]]]:
        """Get a project with all its tasks."""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return None

        tasks = await self.get_tasks_by_project(project_id, user_id)
        return (project, tasks)