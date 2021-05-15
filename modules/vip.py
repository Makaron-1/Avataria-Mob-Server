from modules.base_module import Module

class_name = "Vip"

class Vip(Module):
    prefix = 'vp'
    def __init__(self, server):
        self.server = server
        self.commands = {'buy': self.vip_buy}

    async def vip_buy(self, msg, client):
        return await client.send({'broadcast': False, 'text': f'Купить премиум можно в телеграмме: @gromov_cheater'}, type_=36)
