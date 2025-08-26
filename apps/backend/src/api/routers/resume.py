from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

router = APIRouter()


class Education(BaseModel):
    degree: str
    school_name: str
    start_date: str
    end_date: str
    city: str | None = None
    country: str | None = None
    points: List[str] = []


class Experience(BaseModel):
    job_title: str
    company_name: str
    start_date: str
    end_date: str | None = None
    location: str | None = None
    description: str | None = None
    key_points: List[str] = []


class Project(BaseModel):
    project_name: str
    role: str
    start_date: str
    end_date: str | None = None
    location: str | None = None
    description: str | None = None
    key_points: List[str] = []


class Resume(BaseModel):
    id: str  # In production this would be a UUID, for dummy data we use version
    user_id: str
    job_id: str
    version: str
    full_name: str
    email: str
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    education: List[Education]
    experience: List[Experience]
    projects: List[Project]
    skills: List[str]
    created_at: datetime
    updated_at: datetime


class ResumeListItem(BaseModel):
    version: str
    created_at: datetime
    updated_at: datetime
    description: str


def get_dummy_resume(user_id: str, job_id: str, version: str = "1.0.0") -> Resume:
    """Generate dummy resume data"""
    return Resume(
        id=version,  # Using version as ID for dummy data
        user_id=user_id,
        job_id=job_id,
        version=version,
        full_name="John Doe",
        email="john.doe@example.com",
        phone="+1 (555) 123-4567",
        location="San Francisco, CA",
        summary="Experienced software engineer with a passion for building scalable web applications and solving complex problems.",
        education=[
            Education(
                degree="Bachelor of Science in Computer Science",
                school_name="Stanford University",
                start_date="2018",
                end_date="2022",
                city="Stanford",
                country="USA",
                points=["GPA: 3.8/4.0", "Dean's List", "Computer Science Student Association"]
            )
        ],
        experience=[
            Experience(
                job_title="Senior Software Engineer",
                company_name="Tech Corp",
                start_date="2022",
                end_date=None,
                location="San Francisco, CA",
                description="Leading backend development for enterprise applications",
                key_points=[
                    "Designed and implemented microservices architecture serving 1M+ users",
                    "Reduced API response time by 40% through optimization",
                    "Mentored junior developers and conducted code reviews"
                ]
            ),
            Experience(
                job_title="Software Engineer Intern",
                company_name="Startup Inc",
                start_date="2021",
                end_date="2022",
                location="Remote",
                description="Full-stack development for SaaS platform",
                key_points=[
                    "Built RESTful APIs using Node.js and Express",
                    "Developed React components for dashboard features",
                    "Implemented CI/CD pipeline using GitHub Actions"
                ]
            )
        ],
        projects=[
            Project(
                project_name="Open Source Contribution",
                role="Core Contributor",
                start_date="2023",
                end_date=None,
                description="Contributing to popular open-source project",
                key_points=[
                    "Fixed critical security vulnerabilities",
                    "Added new features requested by community",
                    "Improved documentation and test coverage"
                ]
            )
        ],
        skills=["Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@router.get("/users/{user_id}/jobs/{job_id}/resumes/")
async def list_resume_versions(user_id: str, job_id: str) -> List[ResumeListItem]:
    """List all resume versions for a specific job"""
    return [
        ResumeListItem(
            version="1.0.0",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description="Initial resume version"
        ),
        ResumeListItem(
            version="1.1.0",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description="Updated with new experience"
        ),
        ResumeListItem(
            version="2.0.0",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description="Major revision for senior position"
        )
    ]


@router.get("/users/{user_id}/jobs/{job_id}/resumes/{version}")
async def get_resume_version(user_id: str, job_id: str, version: str) -> Resume:
    """Get a specific resume version"""
    if version not in ["1.0.0", "1.1.0", "2.0.0", "latest"]:
        raise HTTPException(status_code=404, detail=f"Resume version {version} not found")
    
    actual_version = "2.0.0" if version == "latest" else version
    return get_dummy_resume(user_id, job_id, actual_version)


@router.post("/users/{user_id}/jobs/{job_id}/resumes/")
async def create_resume_version(user_id: str, job_id: str, resume: Resume) -> Resume:
    """Create a new resume version"""
    new_version = f"{datetime.now().strftime('%Y%m%d')}.0.0"
    resume.id = new_version  # Using version as ID for dummy data
    resume.user_id = user_id
    resume.job_id = job_id
    resume.version = new_version
    resume.created_at = datetime.now()
    resume.updated_at = datetime.now()
    return resume


@router.get("/users/{user_id}/jobs/{job_id}/resume")
async def get_latest_resume(user_id: str, job_id: str) -> Resume:
    """Get the latest resume version (backward compatibility)"""
    return get_dummy_resume(user_id, job_id, "2.0.0")