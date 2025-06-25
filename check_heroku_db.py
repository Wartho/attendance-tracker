import os
from sqlalchemy import create_engine, text

# Heroku Postgres URL
HEROKU_DB = 'postgres://ubfrspoi93klk9:pc9fbefc60f593eeb9fe6b1fef74e4189255b577406e51c48e56a95adba91ec1d@cer3tutrbi7n1t.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/ddll5a5crrf8sp'
if HEROKU_DB.startswith('postgres://'):
    HEROKU_DB = HEROKU_DB.replace('postgres://', 'postgresql://', 1)

def check_heroku_db():
    engine = create_engine(HEROKU_DB)
    
    with engine.connect() as conn:
        # Check what tables exist
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        print(f"Tables in Heroku DB: {tables}")
        
        # Check structure of each table
        for table in tables:
            print(f"\nStructure of {table}:")
            result = conn.execute(text(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position"))
            for row in result:
                print(f"  {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")

if __name__ == '__main__':
    check_heroku_db() 