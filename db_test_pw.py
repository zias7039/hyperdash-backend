import sqlalchemy
import urllib.parse
from sqlalchemy import create_engine

# try 1: no brackets
pw1 = urllib.parse.quote_plus("ksj06331!234")
uri1 = f"postgresql://postgres:{pw1}@db.usejaxigevnbeemcenfu.supabase.co:5432/postgres"

# try 2: with brackets
pw2 = urllib.parse.quote_plus("[ksj06331!234]")
uri2 = f"postgresql://postgres:{pw2}@db.usejaxigevnbeemcenfu.supabase.co:5432/postgres"

# try 3: pooler port 6543, no brackets
uri3 = f"postgresql://postgres.usejaxigevnbeemcenfu:{pw1}@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"

for i, uri in enumerate([uri1, uri2, uri3]):
    try:
        engine = create_engine(uri, connect_args={'sslmode': 'require'})
        with engine.connect() as conn:
            print(f"Success URI {i}")
            break
    except Exception as e:
        print(f"Failed URI {i}: ", str(e).split('\n')[0])
