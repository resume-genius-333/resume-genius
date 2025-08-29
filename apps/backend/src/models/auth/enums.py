import enum


class ProviderType(enum.Enum):
    PASSWORD = "password"
    GOOGLE = "google"
    GITHUB = "github"
    LINKEDIN = "linkedin"