def log(*args, client=None, module_id=None, publish=True):
    message = ' '.join(map(str, args))
    print(message)
    if client and module_id:
        client.publish(f"cockpit/{module_id}/logs/boot.py", message)