from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import time

app = FastAPI()

YOUR_EMAIL = "24f2003068@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-cykj61.example.com",
    "*"          # Allows the exam page to access your API
]

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Rate Limiting
# -----------------------------
RATE_LIMIT = 13
WINDOW = 10

client_history = {}

# -----------------------------
# Request Context + Rate Limit
# -----------------------------
@app.middleware("http")
async def middleware(request: Request, call_next):

    # Request ID
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # Client ID
    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    history = client_history.get(client, [])

    history = [t for t in history if now - t < WINDOW]

    if len(history) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"X-Request-ID": request_id}
        )

    history.append(now)

    client_history[client] = history

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# -----------------------------
# Endpoint
# -----------------------------
@app.get("/ping")
def ping(request: Request):

    return {
        "email": YOUR_EMAIL,
        "request_id": request.state.request_id
    }