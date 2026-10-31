FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home lowca && mkdir /data && chown lowca:lowca /data
COPY --chown=lowca:lowca app ./app
ENV DATA_DIR=/data PYTHONUNBUFFERED=1
USER lowca
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; import os; import base64; r=urllib.request.Request('http://127.0.0.1:8000/api/health'); p=os.environ.get('APP_PASSWORD'); r.add_header('Authorization', 'Basic '+base64.b64encode(('lowca:'+p).encode()).decode()) if p else None; urllib.request.urlopen(r)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
