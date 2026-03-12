FROM python:3.12-slim@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c AS backend

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy Poetry configuration files
COPY backend/pyproject.toml backend/poetry.lock* ./

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies only (--no-root skips installing the project itself)
RUN poetry install --only main --no-root

# Copy backend code
COPY backend/src/ ./src/
COPY backend/app/ ./app/
COPY backend/server.py ./
COPY .env.example ./

# Expose backend port
EXPOSE 8000

# -------------------------------------------
FROM oven/bun:1.3.10 AS bun-runtime

# -------------------------------------------
FROM oven/bun:1.3.10 AS frontend-build

WORKDIR /app

# Copy frontend files
COPY package.json bun.lock bunfig.toml ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy frontend source code
COPY app/ ./app/
COPY components/ ./components/
COPY hooks/ ./hooks/
COPY types/ ./types/
COPY public/ ./public/
COPY lib/ ./lib/
COPY tailwind.config.js postcss.config.js next.config.mjs tsconfig.json next-env.d.ts proxy.ts ./

# Build frontend
RUN bun run build

# -------------------------------------------
FROM python:3.12-slim@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c

WORKDIR /app

# Copy backend from the backend stage
COPY --from=backend /app /app
COPY --from=backend /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy built frontend from frontend-build stage
COPY --from=frontend-build /app/.next /app/.next
COPY --from=frontend-build /app/public /app/public
COPY --from=frontend-build /app/node_modules /app/node_modules
COPY --from=frontend-build /app/package.json /app/package.json
COPY --from=frontend-build /app/next.config.mjs /app/next.config.mjs
COPY --from=bun-runtime /usr/local/bin/bun /usr/local/bin/bun

# Install additional packages needed for the final image
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/local/bin/bun /usr/local/bin/bunx

# Create a script to start both services
RUN echo '#!/bin/bash\n\
# Start the backend server in the background\n\
python server.py & \n\
# Start the frontend server\n\
bun run start -- --hostname 0.0.0.0 --port 3000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 8000 3000

# Set environment variables
ENV PYTHONPATH=/app

# Start both services
CMD ["/app/start.sh"]
