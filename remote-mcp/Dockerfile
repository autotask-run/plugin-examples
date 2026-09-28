FROM docker.io/library/python:3.12-alpine@sha256:4c47124a8391cb7a9f571164147d154777cf012a4ece5f86097130d7a4478111

ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --chown=10001:10001 server.py /app/server.py
USER 10001:10001
EXPOSE 8765
CMD ["python", "-u", "/app/server.py", "--host", "0.0.0.0", "--port", "8765"]
