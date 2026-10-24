import json

def emit(data, as_json=False):
    if as_json: print(json.dumps(data,indent=2,sort_keys=True,default=str))
    elif isinstance(data,str): print(data)
    else:
        for k,v in data.items(): print(f'{k}: {v}')
