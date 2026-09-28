FROM docker.m.daocloud.io/library/python:3.12-alpine@sha256:4c47124a8391cb7a9f571164147d154777cf012a4ece5f86097130d7a4478111

ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --chown=10001:10001 remote-tool-provider/server.py /app/remote-tool-provider/server.py
COPY --chown=10001:10001 skill-provider-example/server.py skill-provider-example/provider.py /app/skill-provider-example/
COPY --chown=10001:10001 memory-mcp/server.py /app/memory-mcp/server.py
USER 10001:10001

# The deployment selects exactly one example with an explicit command. Each
# service has its own installation-scoped key supplied by Kubernetes Secret.
