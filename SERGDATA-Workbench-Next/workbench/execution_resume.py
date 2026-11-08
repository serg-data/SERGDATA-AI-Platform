"""Safe scheduling helpers for already-completed approved executions."""

import asyncio


async def run_after_branch_task(branch_id, awaitable_factory, chat_tasks,
                                chat_tasks_lock, tracked_runner, is_shutting_down):
    """Wait for an existing branch chat turn, then start its execution resume.

    The awaitable is created only after the branch becomes available. Normal chat
    requests keep their existing conflict behavior; this helper is specific to
    durable execution-result continuations.
    """
    bid = int(branch_id)
    current = asyncio.current_task()
    while True:
        if is_shutting_down():
            raise asyncio.CancelledError("Workbench is shutting down")
        with chat_tasks_lock:
            existing = chat_tasks.get(bid)
            if existing is current or existing is None or existing.done():
                # Reserve the branch atomically before yielding control. Without
                # this reservation, a new /api/chat request could slip between
                # the availability check and tracked_runner(), causing a 409
                # and leaving the durable result waiting for another poll/restart.
                chat_tasks[bid] = current
                existing = None
        if existing is None:
            return await tracked_runner(bid, awaitable_factory())
        try:
            await asyncio.shield(existing)
        except asyncio.CancelledError:
            # A cancelled previous chat turn is finished; cancellation of this
            # coordinator itself must still propagate to its caller.
            if current and current.cancelling():
                raise
        except Exception:
            # The prior turn failed, but it no longer owns the branch.
            pass
