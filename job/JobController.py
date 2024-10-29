from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ProviderManager import job_dao_provider
from job.Job import JobCreate, JobUpdate, JobRead
from job.JobRepository import JobRepository

router_job = APIRouter(
    prefix="/job",
    tags=["job"],
    responses={404: {"description": "Not found"}},
)

job_dao_provider_dep = Annotated[JobRepository, Depends(job_dao_provider)]


@router_job.post("/")
async def create(job: JobCreate, job_repository: job_dao_provider_dep) -> JobRead:
    try:
        return job_repository.save(job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_job.put("/")
async def create(job: JobUpdate, job_repository: job_dao_provider_dep) -> JobRead:
    try:
        return job_repository.update(job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
