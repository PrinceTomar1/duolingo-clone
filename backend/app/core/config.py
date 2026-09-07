"""Application settings, loaded once from the environment.

Everything that could differ between a laptop, CI and a deployed box lives here
so no other module ever reads ``os.environ`` directly.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed configuration.

    Values come from (in order of precedence) real environment variables, then
    a local ``.env`` file, then the defaults below.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Duolingo Clone API"
    api_v1_prefix: str = "/api/v1"

    # ``DEBUG`` gates the developer-only endpoints (e.g. day simulation).
    debug: bool = True

    # The day simulator is a *demo* affordance, not a debug one, and the two
    # deserve separate switches: a deployment may reasonably want the simulator
    # on (the brief asks for streak logic to be demonstrable) while running with
    # DEBUG off. Left unset it follows ``debug``, so local development is
    # unchanged. Note the simulated clock is process-global and shared by every
    # visitor -- enable it only where that is acceptable.
    enable_demo_clock: bool | None = None

    # SQLite lives beside the backend package so the app is runnable on clone.
    database_url: str = "sqlite:///./duolingo.db"

    # Comma-separated list in the environment, e.g.
    # CORS_ORIGINS="http://localhost:3000,https://my-app.vercel.app"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # --- Gamification knobs -------------------------------------------------
    # Kept in config (not scattered as literals) because these are product
    # decisions that get tuned, and the tests assert against them.
    max_hearts: int = 5
    heart_regen_minutes: int = 30
    base_lesson_xp: int = 10
    perfect_lesson_bonus_xp: int = 5
    xp_per_remaining_heart: int = 2
    default_daily_goal_xp: int = 20
    heart_refill_gem_cost: int = 350

    @property
    def demo_clock_enabled(self) -> bool:
        """Whether ``/dev/*`` is mounted. Falls back to ``debug`` when unset."""
        return self.debug if self.enable_demo_clock is None else self.enable_demo_clock

    @property
    def cors_origin_list(self) -> list[str]:
        """``cors_origins`` split into the list Starlette's middleware wants."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton.

    ``lru_cache`` means the ``.env`` file is parsed once, and tests can clear
    the cache to inject a different environment.
    """
    return Settings()


settings = get_settings()
