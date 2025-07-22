import logging, sys, time
from simconnect import SimConnect
import paho.mqtt.client as mqtt

from config import *


# 📄 Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("simconnect.log", mode='a', encoding='utf-8')
    ]
)

def main():
    logging.info("▶️ Démarrage du script")

    # Connexion SimConnect
    sm = SimConnect()
    subs = sm.subscribe_to(["PLANE_ALTITUDE", "AIRSPEED_INDICATED"], period=1.0)
    logging.info("✅ SimConnect prêt")

    # Setup MQTT
    client = mqtt.Client()
    client.username_pw_set(USER, PASS)
    client.on_connect = lambda c, u, f, rc: (c.subscribe(TOPIC_LIGHT), logging.info("✅ MQTT connecté"))
    client.on_message = lambda c, u, msg: handle_light(msg, sm)
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    try:
        while True:
            data = subs.get()
            alt = data.get("PLANE_ALTITUDE")
            spd = data.get("AIRSPEED_INDICATED")
            ts = time.strftime("%Y-%m-%d %H:%M:%S")

            if alt is not None:
                client.publish(TOPIC_ALT, f"{alt:.1f}", qos=1)
                logging.info(f"{ts} • Altitude : {alt:.1f} ft")

            if spd is not None:
                client.publish(TOPIC_SPD, f"{spd:.1f}", qos=1)
                logging.info(f"{ts} • Vitesse : {spd:.1f} kts")

            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("⏹️ Arrêt manuel du script")
    finally:
        client.loop_stop()
        sm.unsubscribe(subs)
        sm.close()

def handle_light(msg, sim: SimConnect):
    payload = msg.payload.decode().strip().lower()
    state = payload in ("true", "1", "on")
    logging.info(f"📩 Reçu {msg.topic} = {payload}")

    cmd = "LANDING_LIGHTS_SET"
    sim.send_event(cmd, int(state))
    logging.info(f"→ Phare d'atterrissage {'ON' if state else 'OFF'} via {cmd}")

if __name__ == "__main__":
    main()
