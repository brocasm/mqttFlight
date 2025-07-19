import os
import config 

def log(client=None, module_id=None , level="INFO", message="", filepath=None):
    

    log_levels = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40
    }

    current_log_level = log_levels.get(config.LOG_LEVEL, 20)
    message_log_level = log_levels.get(level, 20)
    if message_log_level >= current_log_level:        
        print(message)
        if client and module_id:                  
            try:
                client.publish(f"cockpit/{module_id}/logs/{filepath}", message)
            except Exception as e:
                print(f"Failed to publish log: {e}")