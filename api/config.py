from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    # Django settings
    SECRET_KEY: str = (
        "django-insecure-bmje8$xilsz7y5u4(y6x$!v8jb9=!s%=thk@^_qga^nn*9$2nm"
    )
    DEBUG: bool = True
    ALLOWED_HOSTS: list[str] = []

    # Database settings
    DB_NAME: str = "main"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


env = EnvSettings()
