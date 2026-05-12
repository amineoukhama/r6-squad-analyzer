import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MaxNLocator
import textwrap

def generate_mmr_chart(df, output_path="assets/mmr_timeline.png"):
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(9, 5))
    date_strings = pd.to_datetime(df['date']).dt.strftime('%m-%d').tolist()
    banned_cols = ['mmr_change', 'round', 'match_id', 'date']
    player_cols = [col for col in df.select_dtypes(include=['number']).columns if col not in banned_cols]
    colors = ["#007AFF", "#FF9500", "#34C759", "#AF52DE", "#FF3B30"]
    for i, col in enumerate(player_cols):
        color = colors[i % len(colors)]
        label = "You" if col == "current_mmr" else str(col).title()
        ax.plot(date_strings, df[col], color=color, linewidth=2.5, zorder=2)
        ax.scatter(date_strings[-1], df[col].iloc[-1], color=color, s=60, zorder=3)
        ax.text(len(date_strings) - 1 + 0.15, df[col].iloc[-1], f" {label}", 
                color=color, fontsize=10, fontweight='bold', va='center', zorder=4)
    ax.set_title("Squad MMR Timeline", fontsize=16, fontweight='bold', pad=20, color="#1D1D1F")
    ax.set_ylabel("Rank Points (MMR)", fontsize=11, color="#86868B", labelpad=10)
    ax.set_xlabel("")
    ax.grid(axis='y', color='#E5E5EA', linestyle='-', linewidth=1, alpha=0.4, zorder=1)
    ax.grid(axis='x', visible=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    ax.spines['bottom'].set_color("#C6C6C8")
    ax.spines['bottom'].set_linewidth(1.5)
    ax.tick_params(axis='x', colors="#86868B", length=0, labelsize=9, rotation=0)
    ax.tick_params(axis='y', colors="#86868B", length=0)
    all_mmr_values = df[player_cols].values.flatten()
    if len(all_mmr_values) > 0:
        min_mmr = min(all_mmr_values)
        max_mmr = max(all_mmr_values)
        padding = (max_mmr - min_mmr) * 0.5 if max_mmr != min_mmr else 100
        ax.set_ylim(min_mmr - padding, max_mmr + padding)
    ax.set_xlim(-0.5, len(date_strings) + 0.8)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, transparent=False, facecolor="white")
    plt.close()
    return output_path

def generate_map_chart(stats_df, output_path="assets/map_win_rates.png"):
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(10, 6))
    maps = stats_df.index
    x = np.arange(len(maps))
    width = 0.35
    ax.bar(x - width/2, stats_df['Win'], width, label='Wins', color='#34C759', zorder=3)
    ax.bar(x + width/2, stats_df['Loss'], width, label='Losses', color='#FF3B30', zorder=3)
    ax.set_title("Map Analytics: Objective Ban Guide", fontsize=16, fontweight='bold', pad=25, color="#1D1D1F")
    ax.set_ylabel("Number of Matches", fontsize=11, color="#86868B", labelpad=10)
    ax.set_xticks(x)
    wrapped_maps = [textwrap.fill(m, width=11, break_long_words=False) for m in maps]
    ax.set_xticklabels(wrapped_maps, color="#1D1D1F", fontweight='medium', fontsize=9, ha='center')
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

def generate_carry_chart(leaderboard_data, output_path="assets/carry_leaderboard.png"):
    if not leaderboard_data:
        return None
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(9, 5), facecolor='#FFFFFF')
    df = pd.DataFrame(leaderboard_data)
    df = df.sort_values(by="KD", ascending=False).reset_index(drop=True)
    n = len(df)
    if n == 1: order = [0]
    elif n == 2: order = [1, 0]             
    elif n == 3: order = [1, 0, 2]          
    else: order = [1, 0, 2, 3]              
    ordered_df = df.iloc[order].reset_index(drop=True)
    rank_colors = {
        0: "#FFCC00",
        1: "#A2A2A6",
        2: "#CD7F32",
        3: "#5AC8FA"
    }
    x_names = []
    y_kds = []
    bar_colors = []
    for i in range(len(ordered_df)):
        player_name = ordered_df.iloc[i]['Player']
        actual_rank = df[df['Player'] == player_name].index[0] 
        x_names.append(player_name)
        y_kds.append(ordered_df.iloc[i]['KD'])
        bar_colors.append(rank_colors.get(actual_rank, "#5AC8FA"))
    bars = ax.bar(x_names, y_kds, color=bar_colors, width=0.12, zorder=3)
    ax.set_ylabel("K/D Ratio", fontsize=11, color="#86868B", labelpad=10)
    ax.set_title("Daily Squad MVP", fontsize=16, fontweight='bold', color="#1D1D1F", pad=25)
    ax.grid(axis='y', color='#E5E5EA', linestyle='-', linewidth=1, alpha=0.4, zorder=1)
    ax.grid(axis='x', visible=False)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    ax.spines['bottom'].set_color("#C6C6C8")
    ax.spines['bottom'].set_linewidth(1.5)
    ax.tick_params(colors="#86868B", length=0)
    plt.xticks(fontsize=11, fontweight='medium', color="#86868B")
    max_kd = df['KD'].max()
    padding_y = (max_kd * 0.03) if max_kd > 0 else 0.05
    for i, bar in enumerate(bars):
        player_name = x_names[i]
        actual_rank = df[df['Player'] == player_name].index[0]
        if actual_rank == 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + padding_y, 
                    'KING', ha='center', va='bottom', 
                    fontsize=11, fontweight='black', color='#FFCC00')
    ax.set_ylim(0, (max_kd if max_kd > 0 else 1) * 1.15)
    if n == 1:
        ax.set_xlim(-1.5, 1.5)
    elif n == 2:
        ax.set_xlim(-0.8, 1.8)
    elif n == 3:
        ax.set_xlim(-0.5, 2.5)
    else:
        ax.set_xlim(-0.5, 3.5)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor='#FFFFFF', transparent=False)
    plt.close()
    return output_path