import os
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from httpx import AsyncClient

from ProviderManager import job_dao_provider
from job.Job import JobCreate, JobUpdate, JobRead, JobType, JobStatus
from job.JobRepository import JobRepository

router_job = APIRouter(
    prefix="/job",
    tags=["job"],
    responses={404: {"description": "Not found"}},
)

job_dao_provider_dep = Annotated[JobRepository, Depends(job_dao_provider)]


@router_job.get("/")
async def create(type: JobType, job_repository: job_dao_provider_dep, status: JobStatus = JobStatus.REQUESTED) \
        -> List[JobRead]:
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
async def request(job: JobCreate) -> JobRead:
    url = os.environ["SUMMARY_SCRATCH_URL"]

    async with AsyncClient(timeout=30) as client:
        response = await client.post(url, json=job.model_dump())

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    response_data = response.json()
    return JobRead(**response_data)
