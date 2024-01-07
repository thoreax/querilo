
```bash
python -m uvicorn api.main:app --port 8080 --reload
```
Add .env
```
APP_NAME=QA ENGINE
VERSION=1.0.0
DESCRIPTION=QA ENGINE
WHITELIST=["*"]
...
```