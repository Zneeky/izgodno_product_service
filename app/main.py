import os
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from sqlalchemy import select
from app.api.v1.endpoints import parser
from app.db.seed_categories import seed_categories_from_txt
from app.db.session import AsyncSessionLocal, get_db
from app.models.category import Category

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # This gets the current file's directory: app/main.py -> go up 1 level to izgodno_product_service
#     base_dir = os.path.dirname(os.path.abspath(__file__))
#     txt_path = os.path.join(base_dir, "categories.txt")  # adjust path correctly

#     # If categories.txt is outside the app directory (as it is), go up one more level
#     txt_path = os.path.abspath(os.path.join(base_dir, "..", "categories.txt"))

#     async with AsyncSessionLocal() as session:
#         result = await session.scalar(select(Category.id).limit(1))
#         if result is None:
#             print("🌱 Seeding categories from TXT...")
#             await seed_categories_from_txt(session, txt_path)

#     yield

app = FastAPI(title="Izgodno Product Service")

app.include_router(parser.router, prefix="/api/v1/parser", tags=["Parser"])