"""WebSocket consumer for real-time stock updates."""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class StockConsumer(AsyncWebsocketConsumer):
    """
    WebSocket at ws://localhost:8000/ws/stock/
    Clients receive stock_update events: {type: 'stock_update', product_id: ..., stock_quantity: ...}
    """
    GROUP_NAME = 'stock_updates'

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive(self, text_data):
        # Clients don't send messages; just keep-alive pings accepted
        pass

    # Handler: called when group_send delivers a 'stock_update' type message
    async def stock_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'stock_update',
            'product_id': event.get('product_id'),
            'stock_quantity': event.get('stock_quantity'),
        }))
