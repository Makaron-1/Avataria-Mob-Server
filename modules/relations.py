import time
from modules.base_module import Module
from location import Location

class_name = "Relations"


class Relations(Module):
    prefix = "rl"

    def __init__(self, server):
        self.server = server
        self.commands = {'crs': self.create_relation,
                         'get': self.get_relations,
                         'rmv': self.remove_relation}

    async def get_relations(self, msg, client):
        data = {'data': {"uid": client.uid, "rlts": {}}, 'command': 'rl.get'}
        relations = await self.server.redis.smembers(f"rl:{client.uid}")
        for rl in relations:
            relation = await self._get_relation(client.uid, rl)
            data['data']["rlts"][relation["uid"]] = relation["rlt"]
        await client.send(data)

    async def create_relation(self, msg, client):
        confirms = self.server.modules["cf"].confirms
        if client.uid in confirms and \
              not confirms[client.uid]["completed"]:
            return
        pipe = self.server.redis.pipeline()
        link = f'{client.uid}:{msg["data"]["uid"]}'
        for uid in link.split(":"):
            pipe.sadd(f"rl:{uid}", link)
        pipe.set(f"rl:{link}:p", 0)
        pipe.set(f"rl:{link}:st", int(time.time()))
        pipe.set(f"rl:{link}:ut", int(time.time()))
        pipe.set(f"rl:{link}:s", msg['data']['s'])
        await pipe.execute()
        for uid in link.split(":"):
            rl = await self._get_relation(uid, link)
            if uid in self.server.online:
                tmp = self.server.online[uid]
                await Location(self.server, tmp).refresh_avatar()
                await tmp.send({'data': rl, 'command': 'rl.new'})

    async def _get_relation(self, uid, link):
        if link.split(":")[0] == uid:
            second_uid = link.split(":")[1]
        else:
            second_uid = link.split(":")[0]
        pipe = self.server.redis.pipeline()
        for item in ["p", "st", "ut", "s", "ring"]:
            pipe.get(f"rl:{link}:{item}")
        pipe.get(f"uid:{uid}:note:{second_uid}")
        result = await pipe.execute()
        try:
            rl = {"uid": second_uid, "rlt": {"p": int(result[0]),
                                             "st": int(result[1]),
                                             "ut": int(result[2]),
                                             "s": int(result[3]),
                                             "t": None}}
        except TypeError:
            await self.server.redis.srem(f"rl:{uid}", link)
            return
        if result[4]:
            if rl["rlt"]["s"] // 10 == 6:
                rl["rlt"]["t"] = {"er": result[4]}
            else:
                rl["rlt"]["t"] = {"mr": result[4], "wt": 1}
        if result[5]:
            rl["rlt"]["nt"] = result[5]
        return rl

    async def remove_relation(self, msg, client):
        uid = msg['data']["uid"]
        if uid == client.uid:
            return
        link = None
        for rl in await self.server.redis.smembers(f"rl:{client.uid}"):
            if uid in rl:
                link = rl
                break
        if not link:
            return
        await self._remove_relation(link)

    async def _remove_relation(self, link):
        pipe = self.server.redis.pipeline()
        pipe.delete(f"rl:{link}:p")
        pipe.delete(f"rl:{link}:st")
        pipe.delete(f"rl:{link}:ut")
        pipe.delete(f"rl:{link}:s")
        pipe.delete(f"rl:{link}:t")
        for uid in link.split(":"):
            pipe.srem(f"rl:{uid}", link)
        await pipe.execute()
        for uid in link.split(":"):
            if link.split(":")[0] == uid:
                second_uid = link.split(":")[1]
            else:
                second_uid = link.split(":")[0]
            if uid in self.server.online:
                tmp = self.server.online[uid]
                await Location(self.server, tmp).refresh_avatar()
                await tmp.send({'data': {"uid": second_uid}, 'command': 'rl.rmv'})
