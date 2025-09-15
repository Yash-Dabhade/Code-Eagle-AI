import os
from dotenv import load_dotenv

class Environment:
    def __init__(self):
        load_dotenv()
        
        self.RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
        self.RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
        self.RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
        self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen-coder-2.5:7b")

env=Environment()