import enum


class DegreeType(enum.Enum):
    HIGH_SCHOOL = "high_school"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"
    PROFESSIONAL = "professional"
    CERTIFICATE = "certificate"
    DIPLOMA = "diploma"
    EXCHANGE = "exchange"
    OTHER = "other"


class ProficiencyLevel(enum.Enum):
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class EmploymentType(enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    VOLUNTEER = "volunteer"
    OTHER = "other"


class SkillCategory(enum.Enum):
    PROGRAMMING_LANGUAGE = "programming_language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    TOOL = "tool"
    CLOUD = "cloud"
    SOFT_SKILL = "soft_skill"
    DOMAIN = "domain"
    OTHER = "other"