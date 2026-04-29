import pandas as pd
import os

def load_match_data(filepath):
    """
    Ingests raw JSON match telemetry and returns a sanitized Pandas DataFrame.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CRITICAL: Data file missing at {filepath}")
    
    df = pd.read_json(filepath)
    df['date'] = pd.to_datetime(df['date'])
    
    return df

# --- NEW: Map Aggregation Engine ---
def get_map_stats(df):
    """
    Aggregates raw telemetry to calculate win/loss counts and win rates per map.
    """
    # 1. Cross-Tabulation: Count how many Wins and Losses happened on each Map
    stats = pd.crosstab(df['map'], df['result'])
    
    # 2. Safety Check: If a team has zero losses overall, the 'Loss' column 
    # won't exist in the crosstab, which breaks the math. We force it to exist.
    for col in ['Win', 'Loss']:
        if col not in stats.columns:
            stats[col] = 0
            
    # 3. Feature Engineering: Calculate total matches and the Win Rate percentage
    stats['Total Matches'] = stats['Win'] + stats['Loss']
    stats['Win Rate %'] = (stats['Win'] / stats['Total Matches']) * 100
    
    # 4. Sorting: Order the final table from highest win rate to lowest
    return stats.sort_values(by='Win Rate %', ascending=False)

# The testing block
if __name__ == '__main__':
    target_file = 'data/sample_match_data.json'
    match_df = load_match_data(target_file)
    
    print("Data Pipeline Active.")
    print("\nExecuting Map Analytics:")
    print("-" * 60)
    
    # Run our new mathematical function
    map_analytics = get_map_stats(match_df)
    
    # Print the aggregated table
    print(map_analytics)
    print("-" * 60)