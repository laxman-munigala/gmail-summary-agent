FROM python:3.12-slim AS builder

RUN pip install uv

COPY pyproject.toml uv.lock  /app/

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev


FROM python:3.12-slim AS final

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app /app

COPY . .
ENV PATH="/app/.venv/bin:$PATH"

USER appuser

CMD ["python", "main.py"]