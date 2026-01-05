FROM python:3.10-slim
WORKDIR /app
COPY app.py .
RUN pip install flask prometheus-client
CMD ["python", "app.py"]