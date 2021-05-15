import random
from location import Location
from modules.base_module import Module

class_name = "Craft"


class Craft(Module):
    prefix = "crt"

    def __init__(self, server):
        self.server = server
        self.commands = {"bc": self.buy_component, "prd": self.produce}
        self.craft_items = server.parser.parse_craft()

    async def buy_component(self, msg, client):
        buy_for = msg['data']["itId"]
        if buy_for not in self.craft_items:
            return
        to_buy = {}
        gold = 0
        redis = self.server.redis
        items = self.server.game_items["loot"]
        for item in msg['data']["cmIds"]:
            price = items[item]["gold"]/100
            have = await redis.lindex(f"uid:{client.uid}:items:{item}", 1)
            if not have:
                have = 0
            else:
                have = int(have)
            amount = self.craft_items[buy_for]["items"][item] - have
            if amount <= 0:
                continue
            gold += int(rd(price * amount))
            to_buy[item] = amount
        res = await Location(self.server, client).gen_plr()
        if res['res']['gld'] < gold:
            return
        await redis.set(f"uid:{client.uid}:gld", res['res']['gld']-gold)
        await Location(self.server, client).ntf_res()
        compIts = []
        for item in to_buy:
            await self.server.add_item(client.uid, item, 'lt', to_buy[item])
            compIts.append({"c": to_buy[item], "iid": "", "tid": item})
        await client.send({'data': {'itId': buy_for, "compIts": compIts},
                                                            'command': 'crt.bc'})
        inv = await Location(self.server, client)._get_inventory()
        return await client.send({'data': {'inv': inv}, 'command': 'ntf.inv'})

    async def produce(self, msg, client):
        itId = msg['data']["itId"]
        count = 1
        if itId not in self.craft_items:
            return
        redis = self.server.redis
        for item in self.craft_items[itId]["items"]:
            have = await redis.lindex(f"uid:{client.uid}:items:{item}", 1)
            if not have:
                return
            have = int(have)
            if have < self.craft_items[itId]["items"][item]:
                return
        for item in self.craft_items[itId]["items"]:
            amount = self.craft_items[itId]["items"][item]
            await self.server.take_item(item, client.uid, amount)
        if "views" in self.craft_items[itId] and\
                self.craft_items[itId]["views"]:
            itId = itId + random.choice(self.craft_items[itId]["views"].split(","))
            count = 1
        type_ = ""
        if itId in self.craft_items:
            if 'AvaCoin' in self.craft_items[itId]['items']:
                count_coin = self.craft_items[itId]['items']['AvaCoin']
                await self.server.take_item('AvaCoin', client.uid, count_coin)
                if itId in self.server.clothes:
                    await self.server.modules['a'].change_crt(itId, client.uid)
                type_ = "cls"
        elif itId in self.server.game_items["game"]:
            type_ = "gm"
        elif itId in self.server.game_items['craftedActive']:
            type_ = "act"
        elif itId in self.server.game_items["loot"]:
            type_ = "lt"
        elif itId in self.server.furniture:
            type_ = "frn"
        else:
            if not type_:
                return
            return
        await self.server.add_item(client.uid, itId, type_, count)
        inv = await Location(self.server, client)._get_inventory()
        await client.send({'data': {'inv': inv, 'crIt':  {"c": count,
                                              "lid": "",
                                              "tid": itId}},
                                        'command': 'crt.prd'})
        return await client.send({'data': {'inv': inv}, 'command': 'ntf.inv'})


def rd(x, y=0):
    m = int('1'+'0'*y)
    q = x*m
    c = int(q)
    i = int((q-c)*10)
    if i >= 5:
        c += 1
    return c/m
