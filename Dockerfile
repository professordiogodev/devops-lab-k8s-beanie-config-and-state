# PROVIDED. One image for all five Beanie services: the command decides which one runs
# (python -m beanie gateway|menu|orders|payments|notifications).
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY beanie/requirements.txt .
RUN pip install -r requirements.txt
COPY beanie/beanie ./beanie
# a numeric user, so Kubernetes can verify "runAsNonRoot"
USER 10001
ENTRYPOINT ["python", "-m", "beanie"]
CMD ["gateway"]
