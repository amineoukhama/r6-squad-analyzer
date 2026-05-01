import pandas as pd
import os

def load_match_data(filepath):
    """Ingests raw JSON match telemetry and returns a sanitized Pandas DataFrame."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CRITICAL: Data file missing at {filepath}")
    
    df = pd.read_json(filepath)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    return df

def get_map_stats(df):
    """Aggregates raw telemetry to calculate win/loss counts and win rates per map."""
    stats = pd.crosstab(df['map'], df['result'])
    for col in ['Win', 'Loss']:
        if col not in stats.columns:
            stats[col] = 0
            
    stats['Total Matches'] = stats['Win'] + stats['Loss']
    stats['Win Rate %'] = (stats['Win'] / stats['Total Matches']) * 100
    return stats.sort_values(by='Win Rate %', ascending=False)

# --- NEW: The Synergy Engine ---
def get_synergy_stats(filepath):
    """
    Calculates the win rate of specific Operator pairings.
    Normalizes data so (A + B) is treated identically to (B + A).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CRITICAL: Data file missing at {filepath}")
    
    df = pd.read_json(filepath)
    
    # 1. Normalization: We sort the two operator names alphabetically, 
    # then join them with a ' + '. This ensures 'Ash + Zofia' and 'Zofia + Ash'
    # both become strictly 'Ash + Zofia'.
    df['Duo'] = df.apply(lambda row: ' + '.join(sorted([row['player_1'], row['player_2']])), axis=1)
    
    # 2. Aggregation: Count Wins vs Losses for each unique Duo
    stats = pd.crosstab(df['Duo'], df['result'])
    
    # 3. Safety Check: Ensure Win/Loss columns exist
    for col in ['Win', 'Loss']:
        if col not in stats.columns:
            stats[col] = 0
            
    # 4. Math: Calculate Win Rate and sort by the highest performers
    stats['Total Matches'] = stats['Win'] + stats['Loss']
    stats['Win Rate %'] = (stats['Win'] / stats['Total Matches']) * 100
    
    # Sort primarily by Win Rate, and secondarily by Total Matches to break ties
    return stats.sort_values(by=['Win Rate %', 'Total Matches'], ascending=[False, False])

# The testing block
if __name__ == '__main__':
    synergy_file = 'data/synergy_data.json'
    
    print("Data Pipeline Active.")
    print("\nExecuting Operator Synergy Analytics:")
    print("-" * 65)
    
    # Run our new mathematical function
    synergy_analytics = get_synergy_stats(synergy_file)
    
    # Print the aggregated table
    print(synergy_analytics)
    print("-" * 65)