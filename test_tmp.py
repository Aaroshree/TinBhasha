import tempfile 
import os 
with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as f: 
    f.write(b'test') 
    print(f.name) 
    print(os.path.exists(f.name)) 
