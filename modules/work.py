import random, time
from location import Location
from modules.base_module import Module

class_name = "Work"

class Work(Module):
    prefix = 'w'
    def __init__(self, server):
        self.server = server
        self.commands = {'gr': self.get_room}

    async def get_room(self, msg, client):
        room = f'work_{msg["data"]["wid"]}_{client.uid}'
        await self.server.rooms.join_room(room, client)
        ws = {'st': msg['data']['wid'], 's': random.randint(1, 9999), 'wid': msg['data']['wid'],
                'sttm': int(time.time()), 'w': None}
        if msg['data']['wid'] == 'fortune':
            ws.update({'sid': 'fg1'})
            ws.update({'jp': {'slvr': 0, 'enrg': 0, 'emd': 0, 'gch': 0, 'gld': 0}})
            ws.update({'wr': {'slvr': 0, 'enrg': 0, 'emd': 0, 'gch': 0, 'gld': 0}})
        return await client.send({'data': {'ws': ws, 'rid': client.room}, 'command': 'w.gr'})
