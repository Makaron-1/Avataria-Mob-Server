import time
from location import Location

class Room:
    def __init__(self, server):
        self.server = server

    async def join_room(self, room, client):
        if client.room:
            await self.leave_room(client.room, client)
        prefix = self.get_prefix(room)
        plr = await Location(self.server, client).gen_plr()
        apprnc = await self.server.get_appearance(client.uid)
        clths = await Location(self.server, client).get_clothes(client.uid, type_=2)
        for uid in self.server.online:
            tmp = self.server.online[uid]
            if tmp.room == room:
                await tmp.send({'data': {
                    'plr': {
                        'uid': client.uid, 'locinfo': plr['locinfo'],
                        'apprnc': apprnc, 'clths': clths,
                        'ci': plr['ci'], 'usrinf': plr['usrinf']}},
                    'command': f'{prefix}.r.jn'
                })
                await tmp.send({
                    'zoneId': room,
                    'user': {'roomIds': [room],
                             'name': apprnc['n'],
                             'zoneId': client.zoneId,
                             'userId': client.uid
                             }
                    }, type_=16)
        client.room = room

    async def leave_room(self, room, client):
        prefix = self.get_prefix(room)
        for uid in self.server.online:
            tmp = self.server.online[uid]
            if tmp.room == room:
                await tmp.send({'data': {
                    'uid': client.uid
                }, 'command': f'{prefix}.r.lv'})
                await tmp.send({'user':
                    {'roomIds': [],
                     'name': None,
                     'zoneId': tmp.zoneId,
                     'userId': client.uid
                    },
                    'roomId': room
                }, type_=17)
        client.state = 0
        client.room = ""
        client.action_tag = None
        client.direction = 4
        client.position = (-1.0, -1.0)

    def get_prefix(self, room):
        if 'house' in room:
            prefix = 'h'
        elif 'work' in room:
            prefix = 'w'
        else:
            prefix = 'o'
        return prefix

    async def _get_rooms(self, uid):
        countRooms = 0
        look_time = await self.server.redis.get(f'uid:{uid}:house_close')
        if look_time is None:
            look_time = 0
        else:
            if int(time.time()) - int(look_time) < 0:
                look_time = int(look_time)
            else:
                look_time = 0
                await self.server.redis.delete(f'uid:{uid}:house_close')
        rooms = {'r': [], 'lt': look_time}
        roomsUser = await self.server.redis.smembers(f"rooms:{uid}")
        while len(rooms['r']) < len(roomsUser):
            for item in roomsUser:
                if countRooms == 0:
                    if item != 'livingroom':
                        continue
                else:
                    if item != f'room{countRooms}':
                        continue
                room = await self.server.redis.lrange(f"rooms:{uid}:{item}", 0, -1)
                room_items = await self.get_room_items(uid, item)
                rooms['r'].append({"f": room_items,
                              "w": 13, "id": item, "lev": int(room[1]), "l": 13,
                              "nm": room[0]})
            countRooms += 1
        return rooms

    async def refresh_room(self, roomId, client):
        rooms = await self._get_rooms(client.uid)
        room_items = {}
        for room in rooms['r']:
            if room['id'] == roomId:
                room_items = room
                break
        for uid in self.server.online:
            tmp = self.server.online[uid]
            if tmp.room == client.room:
                await tmp.send({
                    'data': {'rm': room_items},
                    'command': 'h.r.rfr'
                })

    async def get_room_items(self, uid, room):
        names = []
        pipe = self.server.redis.pipeline()
        spipe = self.server.redis.pipeline()
        for name in await self.server.redis.smembers(f"rooms:{uid}:{room}:items"):
            pipe.lrange(f"rooms:{uid}:{room}:items:{name}", 0, -1)
            spipe.smembers(f"rooms:{uid}:{room}:items:{name}:options")
            names.append(name)
        result = await pipe.execute()
        options = await spipe.execute()
        i = 0
        items = []
        name = ""
        lid = 0
        for name in names:
            itemes = []
            for element in name.split("_"):
                if not element.isdigit():
                    itemes.append(element)
                    continue
                lid = element
            name, lid = "_".join(itemes), lid
            item = result[i]
            option = options[i]
            try:
                tmp = {"tpid": name, "x": float(item[0]),
                       "y": float(item[1]), "z": float(item[2]),
                       "d": int(item[3]), "lid": int(lid)}
            except IndexError:
                await self.server.redis.srem(f"rooms:{uid}:{room}:items",
                                      f"{name}_{lid}")
                await self.server.redis.delete(f"rooms:{uid}:{room}:items:"
                                        f"{name}_{lid}")
                continue
            for kek in option:
                if kek == "clrs":
                    item = await self.server.redis.smembers(f"rooms:{uid}:{room}:"
                                                     f"items:{name}_{lid}:"
                                                     f"{kek}")
                else:
                    item = await self.server.redis.get(f"rooms:{uid}:{room}:items:"
                                                f"{name}_{lid}:{kek}")
                tmp[kek] = item
            items.append(tmp)
            i += 1
        return items
