from typing import Optional, List, TYPE_CHECKING
import datetime
import uuid
from sqlalchemy import String, ForeignKey, func, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.models.llm.project import ProjectLLMSchema, ProjectTaskLLMSchema

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .skill import TaskSkillMapping


from pydantic import BaseModel, PrivateAttr


class ProjectSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    project_name: str
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    project_url: str | None = None
    repository_url: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    _orm_entity: Optional["Project"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    project_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    repository_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="projects")
    tasks: Mapped[List["ProjectTask"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    @staticmethod
    def from_llm(
        user_id: str | uuid.UUID,
        project_id: str | uuid.UUID,
        llm_schema: ProjectLLMSchema,
    ):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(project_id, str):
            project_id = uuid.UUID(project_id)
        return Project(
            id=project_id,
            user_id=user_id,
            project_name=llm_schema.project_name,
            description=llm_schema.description,
            start_date=llm_schema.start_date,
            end_date=llm_schema.end_date,
            project_url=str(llm_schema.project_url) if llm_schema.project_url else None,
            repository_url=str(llm_schema.repository_url)
            if llm_schema.repository_url
            else None,
        )

    @property
    def schema(self):
        result = ProjectSchema.model_validate(self)
        result._orm_entity = self
        return result


class ProjectTaskSchema(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    description: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    _orm_entity: Optional["ProjectTask"] = PrivateAttr(default=None)

    class Config:
        from_attributes = True


class ProjectTask(Base):
    __tablename__ = "project_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="tasks")
    skill_mappings: Mapped[List["TaskSkillMapping"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    @staticmethod
    def from_llm(
        user_id: str | uuid.UUID,
        project_id: str | uuid.UUID,
        task_id: str | uuid.UUID,
        llm_schema: ProjectTaskLLMSchema,
    ):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        if isinstance(project_id, str):
            project_id = uuid.UUID(project_id)
        if isinstance(task_id, str):
            task_id = uuid.UUID(task_id)
        return ProjectTask(
            id=task_id,
            project_id=project_id,
            user_id=user_id,
            description=llm_schema.description,
        )

    @property
    def schema(self):
        result = ProjectTaskSchema.model_validate(self)
        result._orm_entity = self
        return result
