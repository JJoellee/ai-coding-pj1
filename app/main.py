from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routes import health, tasks

load_dotenv()

app = FastAPI(
    title="Task Tracker API",
    description="A simple CRUD REST API for tracking tasks (Module 1 learning project).",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Collapse a single custom field-validator error into a plain detail string.

    Model-level `raise ValueError(...)` (e.g. the blank-title rule) should
    surface as `{"detail": "<message>"}`, not Pydantic's nested error list.
    Everything else falls back to FastAPI's default shape.
    """
    errors = exc.errors()
    if len(errors) == 1 and errors[0]["type"] == "value_error":
        message = errors[0]["msg"].removeprefix("Value error, ")
        return JSONResponse(status_code=422, content={"detail": message})
    return JSONResponse(status_code=422, content=jsonable_encoder({"detail": errors}))


app.include_router(health.router)
app.include_router(tasks.router)
