from data_producer.kraken_ws import KrakenPrivateFeedProducer

if __name__ == "__main__":

    producer = KrakenPrivateFeedProducer()
    producer.run()