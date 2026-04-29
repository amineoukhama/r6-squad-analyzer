import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from matplotlib.ticker import MaxNLocator
from data_processor import load_match_data, get_map_stats

def generate_mmr_chart(df, output_path="assets/mmr_timeline.png"):
    """
    Generates a minimalist line chart tracking MMR over time.
    Features horizontal dates, no vertical grids, and faint horizontal lines.
    """
    # 1. Clean slate, no default grids
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(8, 5))

    # Convert dates to short strings so they sit perfectly horizontal and evenly spaced
    date_strings = df['date'].dt.strftime('%m-%d')

    # Plot the line and dots
    ax.plot(date_strings, df['current_mmr'], color="#007AFF", linewidth=2.5, zorder=2)
    colors = df['result'].map({'Win': '#34C759', 'Loss': '#FF3B30'})
    ax.scatter(date_strings, df['current_mmr'], color=colors, s=80, zorder=3, edgecolors="white", linewidth=1.5)

    # Title and Labels
    ax.set_title("MMR Timeline Tracking", fontsize=16, fontweight='bold', pad=20, color="#1D1D1F")
    ax.set_ylabel("Rank Points (MMR)", fontsize=11, color="#86868B", labelpad=10)
    ax.set_xlabel("")

    # --- THE UI UPGRADES ---
    
    # Custom faint horizontal grid, NO vertical grid
    ax.grid(axis='y', color='#E5E5EA', linestyle='-', linewidth=1, alpha=0.4, zorder=1)
    ax.grid(axis='x', visible=False)

    # Clean up spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Solid bottom zero-line
    ax.spines['bottom'].set_visible(True)
    ax.spines['bottom'].set_color("#C6C6C8")
    ax.spines['bottom'].set_linewidth(1.5)

    # Fix the dates: Horizontal and smaller font size to fit cleanly
    ax.tick_params(axis='x', colors="#86868B", length=0, labelsize=9, rotation=0)
    ax.tick_params(axis='y', colors="#86868B", length=0)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, transparent=False, facecolor="white")
    plt.close()
    
    return output_path

def generate_map_chart(stats_df, output_path="assets/map_win_rates.png"):
    """
    Generates a clean, grouped bar chart comparing Wins vs Losses per map.
    Features strict integer Y-axis and faint horizontal UI grids.
    """
    sns.set_theme(style="white") 
    fig, ax = plt.subplots(figsize=(8, 6))

    maps = stats_df.index
    x = np.arange(len(maps))
    width = 0.35

    ax.bar(x - width/2, stats_df['Win'], width, label='Wins', color='#34C759', zorder=3)
    ax.bar(x + width/2, stats_df['Loss'], width, label='Losses', color='#FF3B30', zorder=3)

    ax.set_title("Map Analytics: Objective Ban Guide", fontsize=16, fontweight='bold', pad=25, color="#1D1D1F")
    ax.set_ylabel("Number of Matches", fontsize=11, color="#86868B", labelpad=10)

    ax.set_xticks(x)
    ax.set_xticklabels(maps, color="#1D1D1F", fontweight='medium', ha='center')
    
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    ax.grid(axis='y', color='#E5E5EA', linestyle='-', linewidth=1, alpha=0.4, zorder=1)
    ax.grid(axis='x', visible=False)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    ax.spines['bottom'].set_color("#C6C6C8")
    ax.spines['bottom'].set_linewidth(1.5)

    ax.tick_params(colors="#86868B", length=0)

    max_val = max(stats_df['Win'].max(), stats_df['Loss'].max())
    safe_max = max_val if max_val > 0 else 1 
    ax.set_ylim(0, safe_max * 1.25)
    
    ax.legend(frameon=False, loc='upper right', ncol=2)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, transparent=False, facecolor="white")
    plt.close()

    return output_path

# The testing block
if __name__ == '__main__':
    target_file = 'data/sample_match_data.json'
    
    # Test both renders
    match_df = load_match_data(target_file)
    map_analytics = get_map_stats(match_df)
    
    print("Rendering MMR chart...")
    mmr_path = generate_mmr_chart(match_df)
    print("Rendering Map Analytics chart...")
    map_path = generate_map_chart(map_analytics)
    
    print("Success! Both high-resolution charts saved to the assets folder.")