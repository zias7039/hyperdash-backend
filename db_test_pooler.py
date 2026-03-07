import sqlalchemy
from sqlalchemy import create_engine
import urllib.parse

pw = urllib.parse.quote_plus("ksj06331!234")
uri = f"postgresql://postgres.usejaxigevnbeemcenfu:{pw}@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres"

try:
    engine = create_engine(uri, connect_args={'sslmode': 'require'})
    with engine.connect() as conn:
        print("SUCCESS_CONNECTION")
except Exception as e:
    print("FAILED_CONNECTION:", str(e))
