# Load env variables
import os
from dotenv import load_dotenv

class Environment:
    def __init__(self):
       
        load_dotenv()

        self.GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
        self.RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
        self.RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
        self.RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

env=Environment()