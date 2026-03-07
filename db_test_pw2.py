import sqlalchemy
import urllib.parse
from sqlalchemy import create_engine

pw1 = urllib.parse.quote_plus("ksj06331!234")
uri1 = f"postgresql://postgres:{pw1}@db.usejaxigevnbeemcenfu.supabase.co:5432/postgres"

pw2 = urllib.parse.quote_plus("[ksj06331!234]")
uri2 = f"postgresql://postgres:{pw2}@db.usejaxigevnbeemcenfu.supabase.co:5432/postgres"

uri3 = f"postgresql://postgres.usejaxigevnbeemcenfu:{pw1}@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"

out = ""
for i, uri in enumerate([uri1, uri2, uri3]):
    try:
        engine = create_engine(uri, connect_args={'sslmode': 'require'})
        with engine.connect() as conn:
            out += f"Success URI {i}\n"
    except Exception as e:
        out += f"Failed URI {i}: {str(e).splitlines()[0]}\n"

with open("test_out.txt", "w") as f:
    f.write(out)
