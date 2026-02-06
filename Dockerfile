FROM python:3.12-slim AS backend

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
FROM node:18-alpine AS frontend-build

WORKDIR /app

# Copy frontend files
COPY package.json bun.lockb ./

# Install dependencies
RUN npm install

# Copy frontend source code
COPY app/ ./app/
COPY components/ ./components/
COPY public/ ./public/
COPY lib/ ./lib/
COPY tailwind.config.js next.config.mjs tsconfig.json ./

# Build frontend
RUN npm run build

# -------------------------------------------
FROM python:3.12-slim

WORKDIR /app

# Copy backend from the backend stage
COPY --from=backend /app /app
COPY --from=backend /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy built frontend from frontend-build stage
COPY --from=frontend-build /app/.next /app/.next
COPY --from=frontend-build /app/public /app/public
COPY --from=frontend-build /app/node_modules /app/node_modules
COPY --from=frontend-build /app/package.json /app/package.json

# Install additional packages needed for the final image
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Create a script to start both services
RUN echo '#!/bin/bash\n\
# Start the backend server in the background\n\
python server.py & \n\
# Start the frontend server\n\
npm run start\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 8000 3000

# Set environment variables
ENV PYTHONPATH=/app

# Start both services
CMD ["/app/start.sh"]
