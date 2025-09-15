# Singleton rabbitMQ instance
import pika
from config.env import env

class RabbitMQ_Singleton:
    def __init__(self):
        self.instance = None
        if not self.instance:
            self._create_connection()

    def _create_connection(self):
        credentials = pika.PlainCredentials(env.RABBITMQ_USER, env.RABBITMQ_PASS)
        self.instance = pika.BlockingConnection(pika.ConnectionParameters(host=env.RABBITMQ_HOST, credentials=credentials))

    def get_connection(self):
        if not self.instance or self.instance.is_closed:
            self._create_connection()
        return self.instance

    def close_connection(self):
        if self.instance and not self.instance.is_closed:
            self.instance.close()

rabbitmq_instance = RabbitMQ_Singleton()




