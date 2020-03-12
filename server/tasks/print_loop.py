import time
import asyncio
from starlette.websockets import WebSocket

async def count_forever(start, finish, websocket: WebSocket):
    i = start
    while i<finish:
        try:
                await websocket.send_text(f"{i}")
                await asyncio.sleep(2)
                i += 1
        except:
                raise 

# we get the values by iterating over the generator like so :
# for number in count_forever(10,100):
#     print(number)