import pandas as pd
import sqlite3
import os

def load_match_data_from_db():
    """Reads the SQLite database and safely pivots it for Matplotlib charting."""
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

def get_synergy_stats(filepath):
    """
    Calculates the win rate of specific Operator pairings.
    Normalizes data so (A + B) is treated identically to (B + A).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CRITICAL: Data file missing at {filepath}")
    
    df = pd.read_json(filepath)
    
    df['Duo'] = df.apply(lambda row: ' + '.join(sorted([row['player_1'], row['player_2']])), axis=1)
    
    stats = pd.crosstab(df['Duo'], df['result'])
    
    for col in ['Win', 'Loss']:
        if col not in stats.columns:
            stats[col] = 0
            
    stats['Total Matches'] = stats['Win'] + stats['Loss']
    stats['Win Rate %'] = (stats['Win'] / stats['Total Matches']) * 100
    
    return stats.sort_values(by=['Win Rate %', 'Total Matches'], ascending=[False, False])