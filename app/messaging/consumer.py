import json

import aio_pika
from app.db.session import AsyncSessionLocal
from app.dependencies import get_parser_service
from app.messaging.broker import broker
from app.schemas.product import ProductLookupRequest

EXCHANGE_NAME = "IzgodnoUserService.DTO.MessageModels:ProductLookupRequest"
QUEUE_NAME = "product_lookup_consumer"

async def consume_messages():
    exchange = await broker.channel.declare_exchange(EXCHANGE_NAME, type=aio_pika.ExchangeType.FANOUT, durable=True)
    
    queue = await broker.channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.bind(exchange)

    async def on_message(message: aio_pika.IncomingMessage):
            async with message.process():
                raw = json.loads(message.body)
                inner = raw.get("message", {})
                try:
                    request = ProductLookupRequest(**inner)
                    print("✅ Parsed ProductLookupRequest:", request)
                    # 🔁 Manually construct DB session and service
                    async with AsyncSessionLocal() as db:
                        parser_service = await get_parser_service(db)  # ✅ direct call with manual DB session
                        await parser_service.handle_lookup_request(request)
                        #await db.commit()

                except Exception as e:
                    print("❌ Failed to parse message:", e)

    await queue.consume(on_message)
    print(f"🔁 Bound to exchange '{EXCHANGE_NAME}', consuming on queue '{QUEUE_NAME}'")
