FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY macrovoice ./macrovoice
RUN pip install --no-cache-dir .
ENV MACROVOICE_DB=/data/macrovoice.db
VOLUME /data
EXPOSE 8000
CMD ["uvicorn", "macrovoice.server:app", "--host", "0.0.0.0", "--port", "8000"]
