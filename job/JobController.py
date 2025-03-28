from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query

from ProviderManager import job_repository_provider
from job.Job import JobRead, JobType, JobStatus, JobCreate, JobUpdate
from job.JobRepository import JobRepository

router_job = APIRouter(
    prefix="/job",
    tags=["job"],
    responses={404: {"description": "Not found"}},
)

job_dao_provider_dep = Annotated[JobRepository, Depends(job_repository_provider)]


@router_job.get("/")
async def list(job_repository: job_dao_provider_dep,
               type: JobType = Query(...),
               status: JobStatus = Query(default=JobStatus.REQUESTED)) -> List[JobRead]:
    try:
        return job_repository.list(type, status)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@router_job.post("/request")
async def request(job: JobCreate, job_repository: job_dao_provider_dep) -> JobRead:
    return job_repository.save(job)
