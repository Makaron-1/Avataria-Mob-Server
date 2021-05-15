import operator
from modules.base_module import Module

class_name = "UserRating"

class UserRating(Module):
    prefix = 'ur'
    def __init__(self, server):
        self.server = server
        self.commands = {'get': self.get}

    async def get(self, msg, client):
        users = {}
        max_uid = int(await self.server.redis.get("uids"))
        for i in range(1, max_uid+1):
            hrt = await self.server.redis.get(f"uid:{i}:hrt")
            if not hrt or not await self.server.get_appearance(i):
                continue
            users[i] = int(hrt)
        sorted_users = sorted(users.items(), key=operator.itemgetter(1),
                              reverse=True)
        best_top = []
        i = 1
        for user in sorted_users:
            cr = int(await self.server.redis.get(f"uid:{user[0]}:crt"))
            best_top.append({"uid": user[0], "hr": user[1], "cr": cr})
            if i == 20:
                break
            i += 1
        return await client.send({
            'data': {"bt": best_top},
            'command': 'ur.get'
        })
