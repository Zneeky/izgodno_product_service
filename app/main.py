from fastapi import FastAPI
from app.api.v1.endpoints import parser

app = FastAPI(title="Izgodno Product Service")

app.include_router(parser.router, prefix="/api/v1/parser", tags=["Parser"])
