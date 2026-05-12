import pandas as pd
import sqlite3
import os

def load_match_data_from_db():
    db_path = 'data/bot_database.db'
    
    if not os.path.exists(db_path):
        return pd.DataFrame(columns=['date'])
        
    conn = sqlite3.connect(db_path)
    query = "SELECT date, r6_name, mmr FROM mmr_history"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return pd.DataFrame(columns=['date'])

    pivot_df = df.pivot_table(
        index='date', 
        columns='r6_name', 
        values='mmr', 
        aggfunc='mean'
    ).reset_index()
    
    return pivot_df