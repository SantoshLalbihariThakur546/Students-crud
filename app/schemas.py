"""Pydantic models = request validation + response shape."""
import re
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9 \-]{5,18}[0-9]$")


class _Validators(BaseModel):
    """Field rules shared by the create and update models."""

    @field_validator("name", check_fields=False)
    @classmethod
    def clean_name(cls, v):
        if v is None:
            return v
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("name must be at least 2 characters")
        return v

    @field_validator("date_of_birth", check_fields=False)
    @classmethod
    def check_dob(cls, v):
        if v is None:
            return v
        if v > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        if v.year < 1900:
            raise ValueError("date_of_birth must be 1900 or later")
        return v

    @field_validator("email", check_fields=False)
    @classmethod
    def check_email(cls, v):
        if v is None:
            return v
        v = v.strip().lower()
        if not v:
            return None
        if not EMAIL_RE.match(v):
            raise ValueError("invalid email format")
        return v

    @field_validator("phone", check_fields=False)
    @classmethod
    def check_phone(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not PHONE_RE.match(v):
            raise ValueError("invalid phone number (use 7-20 digits, optional leading +)")
        return v

    @field_validator("course", "address", check_fields=False)
    @classmethod
    def blank_to_none(cls, v):
        if v is None:
            return v
        v = v.strip()
        return v or None


class StudentCreate(_Validators):
    """Full record: used for POST and PUT."""

    name: str = Field(..., min_length=2, max_length=100, examples=["Aarav Sharma"])
    date_of_birth: date = Field(..., examples=["2004-05-17"])
    email: Optional[str] = Field(None, examples=["aarav@example.com"])
    phone: Optional[str] = Field(None, examples=["+91 98765 43210"])
    course: Optional[str] = Field(None, max_length=100, examples=["Computer Science"])
    address: Optional[str] = Field(None, max_length=255)
    enrollment_date: Optional[date] = None

    @model_validator(mode="after")
    def check_record(self):
        if not self.email and not self.phone:
            raise ValueError("provide at least one contact: email or phone")
        if self.enrollment_date and self.enrollment_date < self.date_of_birth:
            raise ValueError("enrollment_date cannot be before date_of_birth")
        return self


class StudentUpdate(_Validators):
    """Partial record: used for PATCH (only send what changes)."""

    name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    enrollment_date: Optional[date] = None


class StudentOut(BaseModel):
    id: int
    name: str
    date_of_birth: date
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None
    created_at: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500,
                          examples=["How many students are there?"])


class AskResponse(BaseModel):
    question: str
    answer: str
    source: str            # "ollama" or "fallback"
    model: Optional[str]
    filters_applied: dict
    records_used: List[dict]
