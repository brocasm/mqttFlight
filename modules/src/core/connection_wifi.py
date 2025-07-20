import network
import time
import config
import uasyncio as asyncio


class WifiConnection:
    def __init__(self, ssid=config.WIFI_SSID, password=config.WIFI_PASSWORD):
        self.ssid = ssid
        self.password = password
        self.wlan = network.WLAN(network.STA_IF)

    async def connect(self):
        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)
        while not self.wlan.isconnected():
            await asyncio.sleep(1)
        print(f"Successfully connected to {self.ssid}")

    async def disconnect(self):
        self.wlan.disconnect()
        self.wlan.active(False)
        print(f"Successfully disconnected from {self.ssid}")

    def status(self):
        if self.wlan.isconnected():
            print(f"Connected to {self.ssid}")
        else:
            print("Not connected to any WiFi network")
