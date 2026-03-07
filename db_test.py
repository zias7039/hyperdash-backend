from sqlalchemy import create_engine
import traceback

engine = create_engine('postgresql://postgres:ksj06331%21234@db.usejaxigevnbeemcenfu.supabase.co:5432/postgres')
try:
    with engine.connect() as conn:
        print("Success!")
except Exception as e:
    with open('db_test_trace.log', 'w') as f:
        f.write(traceback.format_exc())
