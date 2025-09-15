# CodeEagle - AI Code Review Bot

An automated code review bot that integrates with GitHub to provide AI-powered feedback on pull requests.

## Architecture

[GitHub] → Webhook → Publisher Service → RabbitMQ → Consumer Service → Qwen LLM → GitHub Comment

## Project Structure

- `producer/` - Webhook listener that enqueues PR analysis jobs
- `consumer/` - Worker that processes jobs and posts reviews

## Quick Start

### Prerequisites
- Python 3.8+
- RabbitMQ server
- Ollama with Qwen model
- ngrok (for webhook testing)

### Setup

1. **Install dependencies for both services:**
```bash
    cd publisher
    pip install -r requirements.txt
    cp .env.example .env
    # Edit .env with your values

    cd ../consumer
    pip install -r requirements.txt
    cp .env.example .env
    # Edit .env with your values
```

2. **Start RabbitMQ:**
```bash
    docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

3. **Pull Qwen Model**
``` bash
    ollama pull qwen2.5-coder:latest 
```

4. **Start Services**
5. 
``` bash
    # Terminal 1: Publisher
    cd producer
    python run_publisher.py

    # Terminal 2: Consumer
    cd consumer
    python run_consumer.py
```

5. **Expose Webhook with Ngrok**
``` bash
    ngrok http 8000
```

## Features

- GitHub webhook integration
- RabbitMQ job queue with retry logic
- Dead letter queue support
- AI-powered code review with Qwen LLM
- GitHub PR comment posting
- Line-by-line comments
- Security scanning
- Custom rule engine
- LoRA fine-tuning support
