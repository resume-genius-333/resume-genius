"""Repository for persisted LLM selection results."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Iterable, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.db.selection import (
    SelectionItemType,
    SelectionResult,
    SelectionResultItem,
    SelectionResultRecordSchema,
    SelectionTarget,
)


@dataclass(slots=True)
class SelectionItemInput:
    """Simple payload for inserting selection items."""

    profile_item_id: uuid.UUID
    justification: str
    item_type: SelectionItemType
    position: int


class SelectionRepository:
    """Encapsulates CRUD access for selection results."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_selection(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        target: SelectionTarget,
    ) -> Optional[SelectionResultRecordSchema]:
        stmt = (
            select(SelectionResult)
            .options(selectinload(SelectionResult.items))
            .where(SelectionResult.user_id == user_id)
            .where(SelectionResult.job_id == job_id)
            .where(SelectionResult.target == target)
        )
        result = await self.session.execute(stmt)
        selection = result.scalar_one_or_none()
        return selection.schema if selection else None

    async def upsert_selection(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        target: SelectionTarget,
        items: Iterable[SelectionItemInput],
    ) -> SelectionResultRecordSchema:
        stmt = (
            select(SelectionResult)
            .options(selectinload(SelectionResult.items))
            .where(SelectionResult.user_id == user_id)
            .where(SelectionResult.job_id == job_id)
            .where(SelectionResult.target == target)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        selection = result.scalar_one_or_none()

        if selection is None:
            selection = SelectionResult(
                user_id=user_id,
                job_id=job_id,
                target=target,
            )
            self.session.add(selection)
        await self.session.flush()

        await self.session.execute(
            delete(SelectionResultItem).where(
                SelectionResultItem.selection_result_id == selection.id
            )
        )
        for item in items:
            self.session.add(
                SelectionResultItem(
                    selection_result_id=selection.id,
                    profile_item_id=item.profile_item_id,
                    justification=item.justification,
                    item_type=item.item_type,
                    position=item.position,
                )
            )

        await self.session.flush()
        selection = (
            await self.session.execute(
                select(SelectionResult)
                    .options(selectinload(SelectionResult.items))
                    .where(SelectionResult.id == selection.id)
            )
        ).scalar_one()
        return selection.schema

    async def delete_selection(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        target: SelectionTarget,
    ) -> None:
        stmt = (
            select(SelectionResult)
            .where(SelectionResult.user_id == user_id)
            .where(SelectionResult.job_id == job_id)
            .where(SelectionResult.target == target)
        )
        result = await self.session.execute(stmt)
        selection = result.scalar_one_or_none()
        if selection is None:
            return
        await self.session.delete(selection)
