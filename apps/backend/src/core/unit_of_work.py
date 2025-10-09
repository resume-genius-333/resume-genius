"""Unit of Work pattern for managing database transactions."""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.repositories.auth_repository import AuthRepository
from src.repositories.resume_repository import (
    ResumeRepository,
    ResumeMetadataRepository,
    ResumeEducationRepository,
    ResumeWorkExperienceRepository,
    ResumeProjectRepository,
    ResumeSkillRepository,
)
from src.repositories.job_repository import JobRepository
from src.repositories.education_repository import EducationRepository
from src.repositories.work_repository import WorkRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.selection_repository import SelectionRepository
from src.repositories.skill_repository import SkillRepository
from src.repositories.status_repository import StatusRepository
from dependency_injector.wiring import Provide, inject
from src.containers import Container, container

logger = logging.getLogger(__name__)
container.wire(modules=[__name__])


class UnitOfWorkFactory:
    """Unit of Work pattern implementation for managing database sessions."""

    @inject
    def __init__(
        self,
        session_factory: async_sessionmaker = Provide[Container.async_session_factory],
    ):
        """Initialize UnitOfWork with session factory."""
        self.session_factory = session_factory
        self._session: Optional[AsyncSession] = None
        self.auth_repository: Optional[AuthRepository] = None
        self.job_repository: Optional[JobRepository] = None
        # Resume-related repositories
        self.resume_repository: Optional[ResumeRepository] = None
        self.resume_metadata_repository: Optional[ResumeMetadataRepository] = None
        self.resume_education_repository: Optional[ResumeEducationRepository] = None
        self.resume_work_experience_repository: Optional[
            ResumeWorkExperienceRepository
        ] = None
        self.resume_project_repository: Optional[ResumeProjectRepository] = None
        self.resume_skill_repository: Optional[ResumeSkillRepository] = None
        # User profile repositories
        self.education_repository: Optional[EducationRepository] = None
        self.work_repository: Optional[WorkRepository] = None
        self.project_repository: Optional[ProjectRepository] = None
        self.skill_repository: Optional[SkillRepository] = None
        self.selection_repository: Optional[SelectionRepository] = None
        self.status_repository: Optional[StatusRepository] = None

    async def __aenter__(self):
        """Enter async context manager - create session and repositories."""
        logger.debug("Starting new Unit of Work")
        self._session = self.session_factory()
        if not self._session:
            raise RuntimeError("Failed to create session")

        # Initialize repositories with the shared session
        self.auth_repository = AuthRepository(self._session)
        self.job_repository = JobRepository(self._session)

        # Initialize resume-related repositories
        self.resume_repository = ResumeRepository(self._session)
        self.resume_metadata_repository = ResumeMetadataRepository(self._session)
        self.resume_education_repository = ResumeEducationRepository(self._session)
        self.resume_work_experience_repository = ResumeWorkExperienceRepository(
            self._session
        )
        self.resume_project_repository = ResumeProjectRepository(self._session)
        self.resume_skill_repository = ResumeSkillRepository(self._session)

        # Initialize user profile repositories
        self.education_repository = EducationRepository(self._session)
        self.work_repository = WorkRepository(self._session)
        self.project_repository = ProjectRepository(self._session)
        self.skill_repository = SkillRepository(self._session)
        self.selection_repository = SelectionRepository(self._session)
        self.status_repository = StatusRepository(self._session)

        logger.debug("Unit of Work initialized with repositories")
        return UnitOfWork(
            self._session,
            self.auth_repository,
            self.job_repository,
            self.resume_repository,
            self.resume_metadata_repository,
            self.resume_education_repository,
            self.resume_work_experience_repository,
            self.resume_project_repository,
            self.resume_skill_repository,
            self.education_repository,
            self.work_repository,
            self.project_repository,
            self.skill_repository,
            self.selection_repository,
            self.status_repository,
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager - rollback if exception, close session."""
        if exc_type:
            logger.error(f"Exception in Unit of Work: {exc_val}", exc_info=True)
            await self.rollback()
        await self.close()

    async def commit(self):
        """Commit the current transaction."""
        if self._session:
            logger.debug("Committing Unit of Work transaction")
            await self._session.commit()
            logger.debug("Transaction committed successfully")
        else:
            logger.warning("Attempted to commit without active session")

    async def rollback(self):
        """Rollback the current transaction."""
        if self._session:
            logger.debug("Rolling back Unit of Work transaction")
            await self._session.rollback()
            logger.debug("Transaction rolled back")
        else:
            logger.warning("Attempted to rollback without active session")

    async def close(self):
        """Close the session."""
        if self._session:
            logger.debug("Closing Unit of Work session")
            await self._session.close()
            self._session = None
            logger.debug("Session closed")

    @property
    def session(self) -> AsyncSession:
        """Get the current session."""
        if not self._session:
            raise RuntimeError("Unit of Work is not active. Use 'async with' context.")
        return self._session


class UnitOfWork:
    def __init__(
        self,
        session: AsyncSession,
        auth_repository: AuthRepository,
        job_repository: JobRepository,
        resume_repository: ResumeRepository,
        resume_metadata_repository: ResumeMetadataRepository,
        resume_education_repository: ResumeEducationRepository,
        resume_work_experience_repository: ResumeWorkExperienceRepository,
        resume_project_repository: ResumeProjectRepository,
        resume_skill_repository: ResumeSkillRepository,
        education_repository: EducationRepository,
        work_repository: WorkRepository,
        project_repository: ProjectRepository,
        skill_repository: SkillRepository,
        selection_repository: SelectionRepository,
        status_repository: StatusRepository,
    ):
        self._session: AsyncSession = session
        self.auth_repository: AuthRepository = auth_repository
        self.job_repository: JobRepository = job_repository
        self.resume_repository: ResumeRepository = resume_repository
        self.resume_metadata_repository: ResumeMetadataRepository = (
            resume_metadata_repository
        )
        self.resume_education_repository: ResumeEducationRepository = (
            resume_education_repository
        )
        self.resume_work_experience_repository: ResumeWorkExperienceRepository = (
            resume_work_experience_repository
        )
        self.resume_project_repository: ResumeProjectRepository = (
            resume_project_repository
        )
        self.resume_skill_repository: ResumeSkillRepository = resume_skill_repository
        # User profile repositories
        self.education_repository: EducationRepository = education_repository
        self.work_repository: WorkRepository = work_repository
        self.project_repository: ProjectRepository = project_repository
        self.skill_repository: SkillRepository = skill_repository
        self.selection_repository: SelectionRepository = selection_repository
        self.status_repository: StatusRepository = status_repository

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def close(self) -> None:
        await self._session.close()

    @property
    def session(self) -> AsyncSession:
        return self._session
