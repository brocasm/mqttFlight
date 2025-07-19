import os 

def log(*args, client=None, module_id=None):
    message = ' '.join(map(str, args))
    print(message)
    if client and module_id:
        filename = os.path.basename(__file__)        
        try:
            client.publish(f"cockpit/{module_id}/logs/{filename}", message)
        except Exception as e:
            print(f"Failed to publish log: {e}")
