import os 

def log(*args, client=None, module_id=None, publish=True):
    message = ' '.join(map(str, args))
    print(message)
    if client and module_id:
        filename = os.path.basename(__file__)
        client.publish(f"cockpit/{module_id}/logs/{filename}", message)
