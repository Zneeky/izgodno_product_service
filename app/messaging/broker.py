import aio_pika

class RabbitMQBroker:
    def __init__(self, amqp_url: str):
        self.amqp_url = amqp_url
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.amqp_url)
        self.channel = await self.connection.channel()
        print("✅ Connected to RabbitMQ")

    async def close(self):
        if self.connection:
            await self.connection.close()
            print("🔌 RabbitMQ connection closed")

# ✅ Singleton instance to import elsewhere
broker = RabbitMQBroker("amqp://guest:guest@localhost/")