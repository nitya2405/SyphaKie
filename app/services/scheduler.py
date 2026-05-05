"""Background pipeline scheduler — wakes every 60s, runs overdue cron pipelines."""
import asyncio
import logging
from datetime import datetime, timezone
from croniter import croniter

logger = logging.getLogger(__name__)

_task: asyncio.Task | None = None


async def _loop() -> None:
    while True:
        await asyncio.sleep(60)
        try:
            await _tick()
        except Exception as e:
            logger.error("Scheduler tick error: %s", e)


async def _tick() -> None:
    from app.db.session import SessionLocal
    from app.models.pipeline import Pipeline
    from app.models.user import User
    from app.api.pipelines import _execute_pipeline

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        due = db.query(Pipeline).filter(Pipeline.cron_schedule.isnot(None)).all()
        for pl in due:
            try:
                cron = croniter(pl.cron_schedule, pl.last_run_at or pl.created_at)
                next_run = cron.get_next(datetime)
                if next_run.replace(tzinfo=timezone.utc) > now:
                    continue
            except Exception:
                continue

            user = db.query(User).filter(User.id == pl.user_id).first()
            if not user:
                continue

            pl.last_run_at = now
            db.commit()

            logger.info("Scheduler: running pipeline %s (%s)", pl.id, pl.name)
            asyncio.create_task(
                _execute_pipeline(
                    run_id=await _create_run(pl),
                    user_id=str(pl.user_id),
                    steps=pl.steps,
                    input_prompt="",
                    extra_params={},
                    step_prompts=None,
                )
            )
    finally:
        db.close()


async def _create_run(pl) -> str:
    from app.db.session import SessionLocal
    from app.models.pipeline import PipelineRun
    import uuid

    db = SessionLocal()
    try:
        run = PipelineRun(
            id=uuid.uuid4(),
            pipeline_id=str(pl.id),
            user_id=pl.user_id,
            input_prompt="(scheduled)",
            status="running",
            step_outputs={},
        )
        db.add(run)
        db.commit()
        return str(run.id)
    finally:
        db.close()


def start() -> None:
    global _task
    _task = asyncio.create_task(_loop())
    logger.info("Pipeline scheduler started.")


def stop() -> None:
    global _task
    if _task:
        _task.cancel()
        _task = None
