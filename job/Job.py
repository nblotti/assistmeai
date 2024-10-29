import enum
from datetime import date, datetime
from typing import Optional

import pytz
from pydantic import BaseModel, Field
from sqlalchemy import Column, Enum, Integer, String, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class JobStatus(str, enum.Enum):
    NONE = "NONE"
    REQUESTED = "REQUESTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobType(str, enum.Enum):
    SUMMARY = "SUMMARY"
    SCRAP = "SCRAP"


class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)
    job_type = Column(Enum(JobType), nullable=False, default=JobType.SUMMARY)
    target_document_id = Column(Integer, nullable=True)
    owner = Column(String, nullable=False, )
    status = Column(Enum(JobStatus), nullable=True, default=JobStatus.REQUESTED)
    created_on = Column(Date, nullable=True, default=datetime.now(pytz.utc))
    last_update = Column(Date, nullable=True, default=datetime.now(pytz.utc))


class JobBase(BaseModel):
    id: Optional[int] = None

    class Config:
        use_enum_values = True  # This will use enum values when serializing/deserializing


class JobCreate(JobBase):
    source: str
    owner: str
    status: Optional[JobStatus] = JobStatus.REQUESTED
    job_type: Optional[JobType] = JobType.SUMMARY

    class Config:
        use_enum_values = True  # This will use enum values when serializing/deserializing


class JobUpdate(JobBase):
    id: int
    status: JobStatus
    target_document_id: Optional[int] = None
    last_update: Optional[datetime] = Field(default_factory=lambda: datetime.now(pytz.utc))


class JobRead(JobBase):
    source: str
    job_type: Optional[JobType] = JobType.SUMMARY
    target_document_id: Optional[int] = None
    owner: str
    status: Optional[JobStatus] = JobStatus.REQUESTED
    created_on: str
    last_update: str
