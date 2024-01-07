
```bash
python -m uvicorn qa_engine.api.main:app --port 4204 --reload --env-file .env
```
Add .env
```
APP_NAME=QA ENGINE
VERSION=1.0.0
DESCRIPTION=QA ENGINE
WHITELIST=["*"]
...
```