import os
import config 

def log(*args, client=None, module_id=None , level="INFO"):
    message = ' '.join(map(str, args))
    print(message)

    log_levels = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40
    }

    current_log_level = log_levels.get(config.LOG_LEVEL, 20)
    message_log_level = log_levels.get(level, 20)
    if message_log_level >= current_log_level:
        if client and module_id:
            filename = os.path.basename(__file__)        
            try:
                client.publish(f"cockpit/{module_id}/logs/{filename}", message)
            except Exception as e:
                print(f"Failed to publish log: {e}")
