import json
import logging
from typing import List, Literal, Optional
import uuid

from instructor import AsyncInstructor
from pydantic import BaseModel, Field
from src.core.unit_of_work import UnitOfWork
from dependency_injector.wiring import Provide, inject
from src.containers import Container, container
import redis.asyncio as redis

from src.services.status_service import StatusService


container.wire(modules=[__name__])
logger = logging.getLogger(__name__)


class SelectedItem(BaseModel):
    id: uuid.UUID = Field(
        description=(
            "UUID of a profile entity to INCLUDE (education, work, project, skill, certification, award, "
            "publication, volunteer, coursework, etc.). Must exist in the source dataset."
        ),
        json_schema_extra={
            "examples": ["8f9e4a3e-12d9-4c7a-9f31-6c2b9f6b0b1a"],
            "ui_label": "Included entity ID",
        },
    )
    justification: str = Field(
        description=(
            "2–3 sentences explaining why this entity improves fit for the TARGET ROLE. "
            "Tie to 1–3 job requirements/keywords and include concrete evidence (scope, metrics, tech, outcomes). "
            "Guidance by type: "
            "• Education: degree/level match, recency, key coursework/capstone. "
            "• Work/Project: responsibilities, impact/metrics, stack/tools. "
            "• Skill/Certification: proficiency/level, recency, where it was applied."
        ),
        json_schema_extra={
            "ui_hint": "Be specific. Name the matched requirements and quantify impact where possible.",
            "examples": [
                "Included: Backend Engineer role demonstrates ownership of Python/FastAPI ETL with Airflow on GCP; "
                r"directly matches requirements for data pipelines and cloud deployment (handled 50M+ rows, 30% latency drop).",
                "Included: M.S. in CS (2023) aligns with ML/NLP focus; coursework in Deep Learning and IR matches posting.",
            ],
        },
    )


class NotSelectedItem(BaseModel):
    id: uuid.UUID = Field(
        description=(
            "UUID of a profile entity to OMIT (education, work, project, skill, certification, etc.). "
            "Must exist in the source dataset."
        ),
        json_schema_extra={
            "examples": ["2a7b1b5f-41ef-4a6e-a5d3-3a3e5c1a9a2b"],
            "ui_label": "Omitted entity ID",
        },
    )
    justification: str = Field(
        description=(
            "One clear reason for omission such as: irrelevant to core requirements, outdated, low impact, "
            "duplicative/overlaps with a stronger included entity, or space constraints. "
            "Reference the mismatched requirement or the overlapping included entity when applicable."
        ),
        json_schema_extra={
            "ui_hint": "Keep it concise; cite the unmet requirement or duplication if relevant.",
            "examples": [
                "Omitted: focuses on Photoshop/Illustrator, not relevant to backend role.",
                "Omitted: high-school award (2015); outdated and low signal compared to recent achievements.",
            ],
        },
    )


class SelectionResult(BaseModel):
    selected_items: List[SelectedItem] = Field(
        description=(
            "Entities to INCLUDE in the final resume, ordered by relevance (most relevant first) to the target role. "
            "IDs must be unique and must NOT appear in not_selected_items."
        ),
        json_schema_extra={
            "ordering": "relevance_desc",
            "constraints": [
                "IDs unique within selected_items",
                "No overlap with not_selected_items",
            ],
        },
    )
    not_selected_items: List[NotSelectedItem] = Field(
        description=(
            "Entities to OMIT from the final resume, each with a concise reason. "
            "IDs must be unique and must NOT overlap with selected_items."
        ),
        json_schema_extra={
            "constraints": [
                "IDs unique within not_selected_items",
                "No overlap with selected_items",
            ],
        },
    )


type SelectionServiceTarget = Literal[
    "educations", "work_experiences", "projects", "skills"
]


class SelectionService:
    @inject
    def __init__(
        self,
        uow: UnitOfWork,
        instructor: AsyncInstructor = Provide[Container.async_instructor],
        redis_client: redis.Redis = Provide[Container.redis_client],
    ):
        self.uow = uow
        self.instructor = instructor
        self.redis_client = redis_client
        self.status_service = StatusService()

    def _get_selection_key(
        self, user_id: uuid.UUID, job_id: uuid.UUID, target: SelectionServiceTarget
    ) -> str:
        return f"user:{user_id}:job:{job_id}:target:{target}:selection"

    async def _set(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        target: SelectionServiceTarget,
        selection: SelectionResult,
    ):
        key = self._get_selection_key(user_id=user_id, job_id=job_id, target=target)
        logger.info(f"!!!!!!!!!!!!!!!!!!!!!!! SETTING [{key}] !!!!!!!!!!!!!!!!!!!!!!!")
        await self.redis_client.set(key, selection.model_dump_json())

    async def _get(
        self, user_id: uuid.UUID, job_id: uuid.UUID, target: SelectionServiceTarget
    ) -> Optional[SelectionResult]:
        key = self._get_selection_key(user_id=user_id, job_id=job_id, target=target)
        logger.info(f"!!!!!!!!!!!!!!!!!!!!!!! GETTING [{key}] !!!!!!!!!!!!!!!!!!!!!!!")
        result = await self.redis_client.get(key)
        if result is None:
            logger.warning("No results found for selection.")
            return None
        if not isinstance(result, str):
            logger.warning(
                f"Received unsupported result type: {type(result)}: {result}"
            )
            return None
        logger.info("Received %s selection result: %s", target, result)
        return SelectionResult.model_validate_json(result)

    async def select_educations(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        job_description: str,
    ) -> SelectionResult:
        logger.info(
            "Selecting educations for user_id=%s, job_id=%s", user_id, job_id
        )
        # ask AI to give us back the information using instructor
        educations = await self.uow.education_repository.get_educations_by_user(user_id)
        logger.info(f"Found {len(educations)} educations.")
        selection_result = await self.instructor.create(
            model="claude-4-sonnet",
            response_model=SelectionResult,
            messages=[
                {
                    "role": "user",
                    "content": f"""
Please help me select the relevant education experiences based on the job description.
You shouldn't omit important education experiences like undergraduate and master degrees, but add
justifications and highlights to each experience.

Here is the job description:

{job_description}

Here are the educations:

{"\n".join(map(lambda x: x.model_dump_json(), educations))}
""",
                }
            ],
        )
        logger.info(
            "AI selected educations: %s",
            selection_result.model_dump_json(indent=2),
        )
        await self._set(
            user_id=user_id,
            job_id=job_id,
            target="educations",
            selection=selection_result,
        )
        await self.status_service.set_and_publish_status(
            user_id=user_id, job_id=job_id, tag="educations-selected-at"
        )
        return selection_result

    async def get_selected_educations(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> Optional[SelectionResult]:
        result = await self._get(user_id=user_id, job_id=job_id, target="educations")
        logger.info(
            f"Received result: {result.model_dump_json(indent=2) if result else 'no result'}"
        )
        return result

    async def select_work_experiences(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        job_description: str,
    ) -> SelectionResult:
        logger.info(
            "Selecting work experiences for user_id=%s, job_id=%s", user_id, job_id
        )
        # ask AI to give us back the information using instructor
        work_experiences = await self.uow.work_repository.get_work_experiences_by_user(
            user_id
        )
        logger.info(f"Found {len(work_experiences)} work experiences.")
        selection_result = await self.instructor.create(
            model="claude-4-sonnet",
            response_model=SelectionResult,
            messages=[
                {
                    "role": "user",
                    "content": f"""
Please help me select the most relevant work experiences based on the job description.
Do not omit foundational roles—such as recent full-time positions, key promotions, or leadership assignments—that demonstrate the core qualifications.
Provide a justification for each experience that highlights responsibilities, impact, metrics, and technologies tied to the job requirements.

Here is the job description:

{job_description}

Here are the work experiences:

{"\n".join(map(lambda x: x.model_dump_json(), work_experiences))}
""",
                }
            ],
        )
        logger.info(
            "AI selected work experiences: %s",
            selection_result.model_dump_json(indent=2),
        )
        await self._set(
            user_id=user_id,
            job_id=job_id,
            target="work_experiences",
            selection=selection_result,
        )
        await self.status_service.set_and_publish_status(
            user_id=user_id, job_id=job_id, tag="work-experiences-selected-at"
        )
        return selection_result

    async def get_selected_work_experiences(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> Optional[SelectionResult]:
        result = await self._get(
            user_id=user_id, job_id=job_id, target="work_experiences"
        )
        logger.info(
            f"Received result: {result.model_dump_json(indent=2) if result else 'no result'}"
        )
        return result

    async def select_projects(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        job_description: str,
    ) -> SelectionResult:
        logger.info("Selecting projects for user_id=%s, job_id=%s", user_id, job_id)
        projects = await self.uow.project_repository.get_projects_by_user(user_id)
        logger.info("Found %d projects.", len(projects))
        selection_result = await self.instructor.create(
            model="claude-4-sonnet",
            response_model=SelectionResult,
            messages=[
                {
                    "role": "user",
                    "content": f"""
Please help me select the most relevant projects based on the job description.
Keep cornerstone projects that showcase measurable impact, modern tooling, and leadership—even if they predate the most recent work history.
For each included project, provide a justification that ties outcomes, metrics, and technologies back to the job requirements.

Here is the job description:

{job_description}

Here are the projects:

{"\n".join(map(lambda x: x.model_dump_json(), projects))}
""",
                }
            ],
        )
        logger.info(
            "AI selected projects: %s", selection_result.model_dump_json(indent=2)
        )
        await self._set(
            user_id=user_id, job_id=job_id, target="projects", selection=selection_result
        )
        await self.status_service.set_and_publish_status(
            user_id=user_id, job_id=job_id, tag="projects-selected-at"
        )
        return selection_result

    async def get_selected_projects(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> Optional[SelectionResult]:
        result = await self._get(user_id=user_id, job_id=job_id, target="projects")
        logger.info(
            f"Received result: {result.model_dump_json(indent=2) if result else 'no result'}"
        )
        return result

    async def select_skills(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        job_description: str,
    ) -> SelectionResult:
        logger.info("Selecting skills for user_id=%s, job_id=%s", user_id, job_id)
        user_skills = await self.uow.skill_repository.get_user_skills(
            user_id, include_skill_details=True
        )
        logger.info("Found %d skills.", len(user_skills))

        skills_payload: List[dict] = []
        for skill in user_skills:
            data = skill.model_dump(mode="json")
            orm_entity = getattr(skill, "_orm_entity", None)
            nested_skill = getattr(orm_entity, "skill", None) if orm_entity else None
            if nested_skill:
                data["skill_name"] = nested_skill.skill_name
                data["skill_category"] = nested_skill.skill_category.value
            skills_payload.append(data)

        skills_json_payload = "\n".join(json.dumps(item) for item in skills_payload)

        selection_result = await self.instructor.create(
            model="claude-4-sonnet",
            response_model=SelectionResult,
            messages=[
                {
                    "role": "user",
                    "content": f"""
Please help me select the most relevant skills based on the job description.
Prioritize skills that align with core requirements, highlight advanced proficiency, and note where they've been applied in recent roles or projects.
Group closely related skills together where it helps show depth, but avoid duplicating essentially identical capabilities.

Here is the job description:

{job_description}

Here are the skills:

{skills_json_payload}
""",
                }
            ],
        )
        logger.info(
            "AI selected skills: %s", selection_result.model_dump_json(indent=2)
        )
        await self._set(
            user_id=user_id, job_id=job_id, target="skills", selection=selection_result
        )
        await self.status_service.set_and_publish_status(
            user_id=user_id, job_id=job_id, tag="skills-selected-at"
        )
        return selection_result

    async def get_selected_skills(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> Optional[SelectionResult]:
        result = await self._get(user_id=user_id, job_id=job_id, target="skills")
        logger.info(
            f"Received result: {result.model_dump_json(indent=2) if result else 'no result'}"
        )
        return result
