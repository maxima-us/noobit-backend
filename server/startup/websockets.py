from server import settings
import asyncio
import websockets
import logging
import ujson
import stackprinter
from collections import deque

from exchanges.kraken.rest.api import KrakenRestAPI as Api


public_ws_url = "wss://ws.kraken.com"
private_ws_url = "wss://ws-auth.kraken.com"


# ================================================================================
# ================================================================================
# ================================================================================
# ================================================================================
# ================================================================================



class KrakenPrivateFeedReader(object):

    def __init__(self, api: Api, feeds: list=["openOrders", "ownTrades"], ws_uri: str="wss://ws-auth.kraken.com"):

        self.ws_uri = ws_uri
        self.feeds = feeds
        self.api = api
        self.open_ws = None
        self.filtered_msgs = {}
       
        self.filtered_msgs["events"] = deque()
        self.filtered_msgs["status"] = deque()
        
        for feed in feeds :
            self.filtered_msgs[feed] = deque()



    async def connect_to_ws(self, ping_interval: int=10, ping_timeout: int=40):
        """Establish Connection with WS

        Args:
            ping_interval (int): in seconds
                optional - default : 20
            ping_timeout (int): in seconds
                optional - default : 20

        Returns:
            websocket connection message (dict)

        """

        self.open_ws = await websockets.connect(uri=self.ws_uri,
                                                ping_interval=ping_interval,
                                                ping_timeout=ping_timeout
                                                )
        
        await asyncio.sleep(0.2)

        if self.open_ws.open:

            ws_status = await self.open_ws.recv()         
            # should return {"connectionID":16078901252266638313,"event":"systemStatus",
            #                "status":"online","version":"1.0.0"}
            logging.info(f"Private WS - Connection :\n{13*' '}Status: {ws_status}")
            await asyncio.sleep(0.1)
            return ws_status
        
        else: 
            logging.info("Couldn't establish connection to WS, retrying ...")
            await asyncio.sleep(0.5)
            await self.connect_to_ws(ping_interval, ping_timeout)


    async def close(self):
        """Close connection to websocket
        """
        
        try:
            await self.open_ws.close()

        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))


    async def subscribe(self):
        """Subscribe to feeds

        Returns:
            Subscription status
        """
        
        ws_token = await self.api.get_websocket_auth_token()
        
        for feed in self.feeds:

            try:
                data = {"event": "subscribe", "subscription": {"name": feed, "token": ws_token['token']}}
                payload = ujson.dumps(data) 
                await self.open_ws.send(payload)
                await asyncio.sleep(0.1)
            
            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))

        await asyncio.sleep(1)
        for _ in range(0,len(self.feeds)) :   
            try:    
                sub_response = await self.read_feed("status") 
                sub_status = sub_response["status"]
                channel_name = sub_response["channelName"]
                logging.info(f"Private WS - Channel : {channel_name}\n{13*' '}Status: {sub_status}") 
            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))


    async def receive_ws_event(self):
        """Read events from WS and dispatch to appropriate deque
        """
        pass

    async def receive_from_ws(self):
        """Read messages from WS and dispatch to appropriate deque
        """

        msg = await self.open_ws.recv()         # returns json string


        if "subscription" in msg:
            msg = ujson.loads(msg)
            self.filtered_msgs["status"].append(msg) 
            return 

        elif "event" in msg:
            msg = ujson.loads(msg)
            self.filtered_msgs["events"].append(msg)
            return 

        else : 
            msg = ujson.loads(msg)
            data = msg[0]
            feed = msg[1]
            self.filtered_msgs[feed].append(data)
            return 



        # subscription status messages are dicts
        # data updates are lists with data at [0] and feed name at [1]

        # instance checking is way too slow, better to make sure everything we receive is a dict
        # ==> need to check if event is in json string before deserializing 

        # if isinstance(msg, dict):
        #     if "event" in msg.keys():
        #         self.filtered_msgs["events"].append(msg)
        #         # return msg

        # if "event" in msg.keys():
        #     self.filtered_msgs["events"].append(msg)
        #     return msg

        # else:
        #     data = msg[0]
        #     feed = msg[1]

        #     self.filtered_msgs[feed].append(data)


    async def read_feed(self, feed):
        """Read messages from feed deque and return them

        Args:
            feed (str)

        Returns:
            messages (list)
        """

        await self.receive_from_ws()
        
        feed_msgs = self.filtered_msgs[feed]
        
        if feed_msgs:  
            logging.info(feed_msgs.popleft())




# ================================================================================
# ================================================================================
# ================================================================================
# ================================================================================


async def connect_private_websockets(api: Api, feeds: list=["ownTrades", "openOrders"]):
    """Connect to private exchange websocket feeds
    
    Args:
        api (Api instance) : api that will be used to get ws auth token
        feeds (List[str]) : list of feeds we want to subscribe to
            optional - default: ["ownTrades", "openOrders"]
    
    Returns 
        websockets.WebSocketClientProtocol
            can be used to send and receive messages

    """

    ws_token = await api.get_websocket_auth_token()

    try: 
        private_ws = await websockets.connect(uri=private_ws_url, ping_interval=15, ping_timeout=60)
        
        await asyncio.sleep(0.2)

        if private_ws.open:
           
            ws_status = await private_ws.recv()         
            # should return {"connectionID":16078901252266638313,"event":"systemStatus","status":"online","version":"1.0.0"}
            logging.info(f"Private WS - Connection :\n{13*' '}Status: {ws_status}")
            await asyncio.sleep(0.1)
            
            for feed in feeds: 
                data = {"event": "subscribe", "subscription": {"name": feed, "token": ws_token['token']}}
                payload = ujson.dumps(data) 
                await private_ws.send(payload)
            
                sub_status = await private_ws.recv() 
                sub_status = ujson.loads(sub_status)
                # should return {"channelName":"ownTrades","event":"subscriptionStatus",
                #                "status":"subscribed","subscription":{"name":"ownTrades"}}
                if "status" in sub_status.keys():
                    sub_status = sub_status["status"]
                
                logging.info(f"Private WS - Channel : {feed}\n{13*' '}Status: {sub_status}") 
                
                snapshot = await private_ws.recv()   
                # do something with it ? 
                await asyncio.sleep(0.1)

        else:
            logging.warning("Websocket not connected yet ... Retrying")
            asyncio.wait(0.5)

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return private_ws






async def connect_public_websockets(pairs: list, feeds: list=["book", "spread"]):
    """Connect to public exchange websocket feeds

    Args:
        pairs (List[str]) : pairs to get the feed data on
            pair has to follow format "XBT/USD"
        feeds (List[str]) : list of feeds we want to subscribe to
            optional - default: ["book", "spread"]
    """

    try: 
        public_ws = await websockets.connect(uri=public_ws_url, ping_interval=15, ping_timeout=60)
        
        await asyncio.sleep(0.2)

        if public_ws.open:
            
            ws_status = await public_ws.recv()         
            # should return {"connectionID":16078901252266638313,"event":"systemStatus","status":"online","version":"1.0.0"}
            logging.info(f"Public WS - Connection :\n{13*' '}Status: {ws_status}")
            await asyncio.sleep(0.1)
            
            for feed in feeds: 
                data = {"event": "subscribe", "pair": pairs, "subscription": {"name": feed}}
                payload = ujson.dumps(data) 
                await public_ws.send(payload)
            
                sub_status = await public_ws.recv()       
                sub_status = ujson.loads(sub_status)  
                # should return {"channelName":"ownTrades","event":"subscriptionStatus",
                #                "status":"subscribed","subscription":{"name":"ownTrades"}}
                if isinstance(sub_status, dict) and "status" in sub_status.keys():
                    sub_status = sub_status["status"]
                
                logging.info(f"Public WS - Channel : {feed}\n{13*' '}Status: {sub_status}") 

                # spread does not send snapshot on sub
                if not feed == "spread":
                    snapshot = await public_ws.recv() 
                    snapshot = ujson.loads(snapshot) 
                    logging.info(f"Public WS - Channel : {feed}\n{13*' '}Snapshot: {snapshot}") 
                # do something with it ? 

        #! no snapshot for book feed, also we need to make sure this executes sequentially


        else:
            logging.warning("Websocket not connected yet ... Retrying")
            asyncio.wait(0.5)

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return public_ws