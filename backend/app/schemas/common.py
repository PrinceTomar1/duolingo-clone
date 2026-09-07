"""Base class shared by every response model."""

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """A response model that can be built straight from a SQLAlchemy row.

    ``from_attributes`` lets FastAPI serialise ORM objects without a manual
    dict-building step, so routers stay short and the schema is the single
    description of the wire format.
    """

    model_config = ConfigDict(from_attributes=True)
