from config.rabbitmq import rabbitmq_instance
import pika
import json

def declare_queues(channel):
    # Main queue
    channel.queue_declare(queue='pr_analysis', durable=True, arguments={
        'x-dead-letter-exchange': 'dlx',
        'x-dead-letter-routing-key': 'dlq.pr_analysis'
    })

    # Dead Letter Exchange and Queue
    channel.exchange_declare(exchange='dlx', exchange_type='direct', durable=True)
    channel.queue_declare(queue='dlq.pr_analysis', durable=True)
    channel.queue_bind(exchange='dlx', queue='dlq.pr_analysis', routing_key='dlq.pr_analysis')

def enqueue_job(job_data: dict):
    # Singleton RabbitMQ instance
    channel = rabbitmq_instance.get_connection().channel()
    declare_queues(channel)

    channel.basic_publish(
        exchange='',
        routing_key='pr_analysis',
        body=json.dumps(job_data),
        properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
    )

    rabbitmq_instance.close_connection()