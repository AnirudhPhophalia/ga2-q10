from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import time

app = FastAPI()

EMAIL = "24f2003068@ds.study.iitm.ac.in"

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-cykj61.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# -----------------------------
# Rate Limit Settings
# -----------------------------
RATE_LIMIT = 13
WINDOW = 10

client_history = {}

# -----------------------------
# Request Context + Rate Limit
# -----------------------------
@app.middleware("http")
async def middleware(request: Request, call_next):

    # Allow CORS preflight without rate limiting
    if request.method == "OPTIONS":
        return await call_next(request)

    # Request ID
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # Rate limiting
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    history = client_history.get(client_id, [])

    # Keep only requests from last 10 seconds
    history = [t for t in history if now - t < WINDOW]

    if len(history) >= RATE_LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        response.headers["X-Request-ID"] = request_id
        return response

    history.append(now)
    client_history[client_id] = history

    response = await call_next(request)

    # Echo request ID in response header
    response.headers["X-Request-ID"] = request_id

    return response


# -----------------------------
# GET /ping
# -----------------------------
@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
