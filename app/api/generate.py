import uuid as _uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import update as _sa_update
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_current_api_key, get_db
from app.schemas.generate import GenerateRequest, GenerateResponse
from app.services.generate import GenerationService
from app.models.user import User
from app.models.api_key import ApiKey
from app.models.job import Job

router = APIRouter()


async def _run_job(job_id: str, user_id: str, request: GenerateRequest) -> None:
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == _uuid.UUID(job_id)).first()
        if not job:
            return
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        user = db.query(User).filter(User.id == _uuid.UUID(user_id)).first()
        service = GenerationService(db)
        result = await service.run(user=user, request=request)

        job.status = "success"
        job.modality = result.modality
        job.model_id = result.model
        job.provider = result.provider
        job.output_url = result.output.url
        job.output_content = result.output.content
        job.credits_used = result.meta.credits_used
        job.request_id = result.request_id
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as e:
        try:
            db.rollback()
            job = db.query(Job).filter(Job.id == _uuid.UUID(job_id)).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


async def _run_batch_job(job_id: str, batch_id: str, user_id: str, request: GenerateRequest) -> None:
    from app.db.session import SessionLocal
    from app.models.batch import Batch
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == _uuid.UUID(job_id)).first()
        if not job:
            return
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        user = db.query(User).filter(User.id == _uuid.UUID(user_id)).first()
        service = GenerationService(db)
        result = await service.run(user=user, request=request)

        job.status = "success"
        job.modality = result.modality
        job.model_id = result.model
        job.provider = result.provider
        job.output_url = result.output.url
        job.output_content = result.output.content
        job.credits_used = result.meta.credits_used
        job.request_id = result.request_id
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as e:
        try:
            db.rollback()
            job = db.query(Job).filter(Job.id == _uuid.UUID(job_id)).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
    finally:
        try:
            from app.models.batch import Batch
            # Atomic increment — avoids read-modify-write race when jobs finish concurrently.
            succeeded = job.status == "success" if job else False
            db.execute(
                _sa_update(Batch)
                .where(Batch.id == _uuid.UUID(batch_id))
                .values(
                    completed=Batch.completed + (1 if succeeded else 0),
                    failed=Batch.failed + (0 if succeeded else 1),
                )
                .execution_options(synchronize_session=False)
            )
            db.commit()
            # Re-read to check whether all jobs are now done and update status.
            batch = db.query(Batch).filter(Batch.id == _uuid.UUID(batch_id)).first()
            if batch and (batch.completed + batch.failed) >= batch.total:
                batch.status = "partial" if batch.failed > 0 else "done"
                db.commit()
        except Exception:
            pass
        db.close()


@router.post("/generate")
async def generate(
    body: GenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    current_key: ApiKey = Depends(get_current_api_key),
    db: Session = Depends(get_db),
):
    if current_key.monthly_credit_limit is not None:
        used = current_key.credits_used_this_month or 0
        if used >= current_key.monthly_credit_limit:
            raise HTTPException(status_code=402, detail={
                "code": "SPENDING_LIMIT_EXCEEDED",
                "message": f"Monthly spending limit of {current_key.monthly_credit_limit} credits reached.",
            })

    if body.async_job:
        job = Job(
            id=_uuid.uuid4(),
            user_id=current_user.id,
            status="queued",
            modality=body.modality,
            input_payload=body.model_dump(exclude={"async_job"}),
        )
        db.add(job)
        db.commit()
        background_tasks.add_task(_run_job, str(job.id), str(current_user.id), body)
        return {"job_id": str(job.id), "status": "queued"}

    service = GenerationService(db)
    result = await service.run(user=current_user, request=body)

    if current_key.monthly_credit_limit is not None:
        current_key.credits_used_this_month = (current_key.credits_used_this_month or 0) + (result.meta.credits_used or 0)
        db.commit()

    # Check auto top-up threshold after credit deduction
    try:
        from app.models.credit import Credit
        from app.api.billing import trigger_auto_topup
        credit = db.query(Credit).filter_by(user_id=current_user.id).first()
        if credit:
            await trigger_auto_topup(db, current_user, credit.balance)
    except Exception:
        pass

    return result


class BatchRequest(BaseModel):
    prompts: List[str]
    modality: str = "text"
    mode: str = "auto"
    model: str | None = None
    task_type: str | None = None
    use_org_credits: bool = False


@router.post("/generate/batch")
async def generate_batch(
    body: BatchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.batch import Batch
    prompts = [p.strip() for p in body.prompts if p.strip()]
    if not prompts:
        raise HTTPException(status_code=400, detail={"code": "NO_PROMPTS", "message": "No prompts provided."})
    if len(prompts) > 50:
        raise HTTPException(status_code=400, detail={"code": "TOO_MANY", "message": "Maximum 50 prompts per batch."})

    batch = Batch(id=_uuid.uuid4(), user_id=current_user.id, total=len(prompts))
    db.add(batch)
    db.flush()

    job_ids = []
    for p in prompts:
        job = Job(
            id=_uuid.uuid4(),
            user_id=current_user.id,
            batch_id=batch.id,
            prompt=p,
            status="queued",
            modality=body.modality,
            input_payload={"prompt": p, "modality": body.modality, "mode": body.mode,
                           **({"model": body.model} if body.model else {}),
                           **({"task_type": body.task_type} if body.task_type else {})},
        )
        db.add(job)
        db.flush()
        req = GenerateRequest(
            prompt=p, modality=body.modality, mode=body.mode,
            model=body.model, task_type=body.task_type,
            use_org_credits=body.use_org_credits,
        )
        background_tasks.add_task(_run_batch_job, str(job.id), str(batch.id), str(current_user.id), req)
        job_ids.append(str(job.id))

    db.commit()
    return {"batch_id": str(batch.id), "job_ids": job_ids, "total": len(prompts)}
