import json

import aio_pika
from app.messaging.broker import broker

EXCHANGE_NAME = "IzgodnoUserService.DTO.MessageModels:ProductLookupRequest"
QUEUE_NAME = "product_lookup_consumer"

async def consume_messages():
    exchange = await broker.channel.declare_exchange(EXCHANGE_NAME, type=aio_pika.ExchangeType.FANOUT, durable=True)
    
    queue = await broker.channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.bind(exchange)

    async def on_message(message: aio_pika.IncomingMessage):
        async with message.process():
            data = json.loads(message.body)
            print(f"📩 Received from .NET: {data}")
            # Call your parser service or anything else here

    await queue.consume(on_message)
    print(f"🔁 Bound to exchange '{EXCHANGE_NAME}', consuming on queue '{QUEUE_NAME}'")
