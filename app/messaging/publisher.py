import json

import aio_pika
from app.messaging.broker import broker

def wrap_mass_transit_message(message_type: str, message_body: dict) -> dict:
    return {
        "messageType": [f"urn:message:{message_type}"],
        "message": message_body
    }

async def publish_message(queue_name: str, message_body: dict, message_type: str):
    await broker.channel.declare_queue(queue_name, durable=True)
    
    # Wrap the message according to MassTransit spec
    mass_transit_message = wrap_mass_transit_message(message_type, message_body)

    await broker.channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(mass_transit_message, default=str).encode(),  # handles UUID, datetime, etc.
            content_type="application/json"
        ),
        routing_key=queue_name
    )