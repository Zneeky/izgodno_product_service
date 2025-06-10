import json

import aio_pika
from app.messaging.broker import broker

async def publish_message(queue_name: str, message: dict):
    await broker.channel.declare_queue(queue_name, durable=True)
    await broker.channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(message).encode()),
        routing_key=queue_name
    )
