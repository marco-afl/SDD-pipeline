from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import datetime, timezone

from src.database import engine, Base
from src.api.routes.transfers import router

# Register models with SQLAlchemy metadata
from src.models import account, transfer, audit_log  # noqa: F401

app = FastAPI(title="NovaPay API", version="1.0.0")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    raw_msg = errors[0].get("msg", "Error de validación.") if errors else "Error de validación."
    msg = raw_msg.replace("Value error, ", "")

    if "mayor a cero" in msg or "2 decimales" in msg:
        error_code = "INVALID_AMOUNT"
    elif "misma" in msg:
        error_code = "SAME_ACCOUNT_TRANSFER"
    else:
        error_code = "VALIDATION_ERROR"

    return JSONResponse(
        status_code=400,
        content={
            "error_code": error_code,
            "message": msg,
            "transfer_id": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


app.include_router(router)
