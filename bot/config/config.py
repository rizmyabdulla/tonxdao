from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    DELAY_IN_SENDING_MESSAGE: float = 0.4
    NUMBER_OF_DISPLAY_MESSAGE: int = 2

    USE_RANDOM_DELAY_IN_RUN: bool = True
    RANDOM_DELAY_IN_RUN: list[int] = [5, 30]

    USE_REF: bool = False
    # REF_ID: str = 'ref_h4OogZKJF4'

    USE_PROXY_FROM_FILE: bool = False


settings = Settings()


