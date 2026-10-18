FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
WORKDIR /workspace
ENTRYPOINT ["n8n-sync"]
CMD ["--help"]
