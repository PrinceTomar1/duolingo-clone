FROM python:3.12-slim

# Bytecode files and stdout buffering are both noise in a container.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies are copied and installed before the source so an application
# edit does not invalidate the pip layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Migrate, seed, then serve -- which makes a fresh container immediately usable.
#
# `--if-empty` seeds only a database with no course yet. A restarted container
# re-runs this command, and an unconditional seed would reset learner progress.
#
# The port comes from $PORT when the platform sets one (Railway does, and routes
# only to that port), falling back to 8000 for local `docker compose`.
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed.seed_data --if-empty && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
