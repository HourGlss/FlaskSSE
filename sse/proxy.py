from sseclient import SSEClient
import ast
while True:
    messages = None
    try:
        messages = SSEClient('http://192.168.1.222:8000/stream')
    except Exception as e:
        print(e)
    if messages is not None:
        for msg in messages:
            # dmsg = ast.literal_eval(str(msg))
            # print(dmsg["message"])
            print(msg)


