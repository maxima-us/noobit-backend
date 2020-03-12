from data_producer.kraken_ws import KrakenPrivateFeedProducer
from data_producer.private_consumer import KrakenPrivateFeedConsumer
import asyncio

producer = KrakenPrivateFeedProducer()
consumer = KrakenPrivateFeedConsumer()

#================================================================================
#================================================================================
#================================================================================
#================================================================================
#================================================================================

# from concurrent.futures import ProcessPoolExecutor



# def run_consumer():
#     asyncio.run(consume())

# with ProcessPoolExecutor(max_workers=6) as executor:
#     executor.submit(kraken.run)
#     executor.submit(run_consumer)



#================================================================================
#================================================================================
#================================================================================
#================================================================================
#================================================================================


import multiprocessing

def run_consumer():
    try:
        consumer.run()
    except KeyboardInterrupt:
        print("Had to stop the consumer")

def run_producer():
    try:
        producer.run()
    except KeyboardInterrupt:
        print("Had to stop the producer")



if __name__ == '__main__':
   
    # original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    # pool = multiprocessing.Pool(2)
    # signal.signal(signal.SIGINT, original_sigint_handler)

    

    # try:
    #     pool.apply_async(consumer.run)
    #     pool.apply_async(producer.run)
    #     time.sleep(10)
    #     pool.close()
    #     pool.join()

    # except KeyboardInterrupt:
    #     print "Caught KeyboardInterrupt, terminating workers"
    #     pool.terminate()
    #     pool.join()

    consumer_process = multiprocessing.Process(target=run_consumer)
    producer_process = multiprocessing.Process(target=run_producer)

    consumer_process.start()
    producer_process.start()
    
    consumer_process.join()
    producer_process.join()