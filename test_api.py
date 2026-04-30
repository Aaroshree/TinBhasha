from core.tmt_client import get_client 
client = get_client() 
result = client.translate('Hello', 'en', 'ne') 
print(result) 
