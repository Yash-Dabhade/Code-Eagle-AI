import json
from config.env import env
from config.rabbitmq import rabbitmq_instance
from workers.pr_analysis_worker import process_job
from utils.logger import setup_logger

logger = setup_logger(__name__)

def start_consuming():
    connection = rabbitmq_instance.get_connection()
    channel = connection.channel()

    # Declare queues (same as publisher)
    channel.queue_declare(queue='pr_analysis', durable=True, arguments={
        'x-dead-letter-exchange': 'dlx',
        'x-dead-letter-routing-key': 'dlq.pr_analysis'
    })
    
    channel.exchange_declare(exchange='dlx', exchange_type='direct', durable=True)
    channel.queue_declare(queue='dlq.pr_analysis', durable=True)
    channel.queue_bind(exchange='dlx', queue='dlq.pr_analysis', routing_key='dlq.pr_analysis')

    def callback(ch, method, properties, body):
        
        try:
            job_data = json.loads(body)
            process_job(job_data)
            ch.basic_ack(delivery_tag=method.delivery_tag)
       
        except Exception as e:
            print(f"[ERROR] Failed to process job: {e}")
            # Reject and requeue (up to 3 times)
            if method.redelivered:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)  # Send to DLQ
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)   # Retry

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='pr_analysis', on_message_callback=callback)
    print("Consumer started. Waiting for messages...")
    channel.start_consuming()