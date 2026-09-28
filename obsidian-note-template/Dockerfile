FROM node:22-bookworm-slim

RUN groupadd --system --gid 10001 autotask \
  && useradd --system --uid 10001 --gid 10001 --home-dir /nonexistent --shell /usr/sbin/nologin autotask

WORKDIR /app
COPY server.mjs template-engine.mjs ./

ENV HOST=0.0.0.0
ENV PORT=8765
ENV NODE_ENV=production
USER 10001:10001
EXPOSE 8765
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD node --input-type=module -e "fetch('http://127.0.0.1:8765/health').then(r => { if (!r.ok) process.exit(1) }).catch(() => process.exit(1))"
ENTRYPOINT ["node", "server.mjs"]
