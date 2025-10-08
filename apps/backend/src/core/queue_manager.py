from asyncio import Lock, Queue, gather
from collections import defaultdict
from typing import Dict
from uuid import UUID, uuid4


class QueueContext:
    def __init__(self, key: str, service: "QueueService") -> None:
        self._key = key
        self._id: UUID | None = None
        self._service = service
        self._queue: Queue | None = None

    async def __aenter__(self):
        if self._id is not None:
            raise RuntimeError("Context already entered")
        self._id, self._queue = await self._service._create_queue(self._key)
        return self._queue

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._id is None:
            raise RuntimeError("Context not entered")
        await self._service._release_queue(self._key, self._id)
        self._id = None
        self._queue = None


class QueueService:
    def __init__(self) -> None:
        self._queues: Dict[str, Dict[UUID, Queue]] = defaultdict(dict)
        self._lock = Lock()

    async def _create_queue(self, key: str) -> tuple[UUID, Queue]:
        queue_id = uuid4()
        queue = Queue()
        async with self._lock:
            self._queues[key][queue_id] = queue
        return queue_id, queue

    async def _release_queue(self, key: str, id: UUID) -> None:
        async with self._lock:
            if key in self._queues and id in self._queues[key]:
                del self._queues[key][id]
                if not self._queues[key]:
                    del self._queues[key]

    def create_listening_context(self, key: str) -> QueueContext:
        return QueueContext(key, self)

    async def notify(self, key: str, message: str) -> None:
        async with self._lock:
            queues = list(self._queues.get(key, {}).values())

        for queue in queues:
            queue.put_nowait(message)

    async def notify_wait(self, key: str, message: str) -> None:
        async with self._lock:
            queues = list(self._queues.get(key, {}).values())

        if not queues:
            return

        await gather(*(queue.put(message) for queue in queues))
