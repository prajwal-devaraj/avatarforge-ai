FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

RUN groupadd --system avatarforge \
    && useradd --system --gid avatarforge --create-home avatarforge

COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/instance/generated /app/instance/jobs \
    && chown -R avatarforge:avatarforge /app

USER avatarforge

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3).read()" || exit 1

ENTRYPOINT ["./docker/entrypoint.sh"]
