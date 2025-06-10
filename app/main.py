import asyncio
from contextlib import asynccontextmanager
import contextlib
from fastapi import FastAPI
from app.api.v1.endpoints import parser, crawler
from app.messaging.broker import broker
from app.messaging.consumer import consume_messages
from app.models.category import Category
from app.logging_config import setup_logging
setup_logging()




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

import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.connect()
    consumer_task = asyncio.create_task(consume_messages())
    yield
    consumer_task.cancel()
    await broker.close()

app = FastAPI(
    title="Izgodno Product Service",
    lifespan=lifespan
)

app.include_router(parser.router, prefix="/api/v1/parser", tags=["Parser"])
app.include_router(crawler.router, prefix="/api/v1/crawler", tags=["Crawler"])