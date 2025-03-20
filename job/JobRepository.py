import json
from datetime import datetime
from typing import Sequence

import pytz
from sqlalchemy import select

from BaseAlchemyRepository import BaseAlchemyRepository
from job.Job import JobCreate, Job, JobUpdate, JobRead, JobType, JobStatus


class JobRepository(BaseAlchemyRepository):

    def save(self, job: JobCreate) -> JobRead:
        new_job = Job(
            source=job.source,
            owner=job.owner,
            job_type=job.job_type

        )
        self.db.add(new_job)
        self.db.commit()
        self.db.refresh(new_job)
        job.id = new_job.id
        return self.map_to_job(new_job)

    def update(self, job: JobUpdate) -> JobRead:
        stmt = select(Job).where(Job.id == int(job.id))
        job_to_update: Job = self.db.execute(stmt).scalars().first()

        if job_to_update:
            job_to_update.status = job.status
            job_to_update.last_update = datetime.now(pytz.utc)
            # Ensure target_document_id is not a tuple
            job_to_update.target_document_id = job.target_document_id or None
            self.db.commit()
            self.db.refresh(job_to_update)

        return self.map_to_job(job_to_update)

    def list(self, type: JobType, status: JobStatus):
        stmt = select(Job).where(Job.job_type == type, Job.status == status)
        jobs: Sequence[Job] = self.db.execute(stmt).scalars().all()

        return [self.map_to_job(doc) for doc in jobs]

    def map_to_job(self, job: Job) -> JobRead:
        return JobRead(
            id=job.id,
            source=job.source,
            job_type=job.job_type,
            target_document_id=job.target_document_id,
            owner=job.owner,
            status=job.status,
            created_on=job.created_on.strftime("%d.%m.%Y"),
            last_update=job.last_update.strftime("%d.%m.%Y"),

            payload=json.loads(job.payload) if job.payload else {}
        )
