import os
import json
import asyncio
import discord
import pandas as pd
from datetime import datetime, timedelta
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from data_processor import load_match_data_from_db
from visualizer import generate_mmr_chart, generate_map_chart, generate_carry_chart
from db_manager import init_db, log_mmr
from tracker_scraper import fetch_recent_matches

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

USERS_FILE = 'data/users.json'

def load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users_data: dict) -> None:
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=4)

def get_session_start():
    now = datetime.now()
    if now.hour < 6:
        return now.replace(hour=6, minute=0, second=0, microsecond=0) - timedelta(days=1)
    else:
        return now.replace(hour=6, minute=0, second=0, microsecond=0)

@bot.event
async def on_ready():
    print(f'System Online: Logged in securely as {bot.user.name}')
    init_db()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} Slash Commands to Discord.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name='ping', description='Check the latency of the bot.')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong! 🏓 Gateway latency: {round(bot.latency * 1000)}ms.')

@bot.tree.command(name='register', description='Link your Discord account to your exact Ubisoft name.')
@app_commands.describe(r6_name="Your exact Ubisoft username")
async def register(interaction: discord.Interaction, r6_name: str):
    discord_id = str(interaction.user.id)
    users = load_users()
    users[discord_id] = r6_name
    save_users(users)
    await interaction.response.send_message(f"✅ **Registration Complete:** Your Discord is now linked to R6 Player: `{r6_name}`")

@bot.tree.command(name='rank', description='Generates an MMR timeline for you and your squad.')
@app_commands.describe(p1="Squad Member 1", p2="Squad Member 2", p3="Squad Member 3")
async def rank(interaction: discord.Interaction, p1: discord.Member = None, p2: discord.Member = None, p3: discord.Member = None):
    await interaction.response.defer()
    users = load_users()
    target_members = [interaction.user]
    if p1: target_members.append(p1)
    if p2: target_members.append(p2)
    if p3: target_members.append(p3)
    players_to_graph = []
    log_messages = []
    for member in target_members:
        discord_id = str(member.id)
        r6_name = users.get(discord_id, member.display_name)
        players_to_graph.append(r6_name)
        df_matches = await fetch_recent_matches(r6_name)
        if not df_matches.empty and 'RP' in df_matches.columns:
            mmr = int(df_matches.iloc[0]['RP'])
            rank_name = "Ranked (Scraped)"
            log_mmr(r6_name, mmr, rank_name)
            log_messages.append(f"✅ Extracted **{mmr}** MMR for {r6_name}")
        else:
            log_messages.append(f"⚠️ Scrape failed for {r6_name}. Using local data if available.")
    try:
        df = load_match_data_from_db()
        valid_columns = ['date']
        for player in players_to_graph:
            if player in df.columns:
                valid_columns.append(player)
            else:
                log_messages.append(f"❌ No history found for `{player}`. Ensure they are registered.")
        if len(valid_columns) == 1:
            await interaction.edit_original_response(content="\n".join(log_messages) + "\n\n**Aborting:** No valid data to graph.")
            return
        filtered_df = df[valid_columns]
        chart_path = generate_mmr_chart(filtered_df)
        discord_file = discord.File(chart_path, filename="mmr_timeline.png")
        header = "**Squad MMR Timeline**\n" + "\n".join(log_messages)
        await interaction.edit_original_response(content=header, attachments=[discord_file])
    except Exception as e:
        await interaction.edit_original_response(content=f"⚠️ **CRITICAL ERROR:** \n`{e}`")

@bot.tree.command(name='mapban', description='Generates a map ban guide. Filters for shared matches if friends are tagged.')
@app_commands.describe(p1="Squad Member 1", p2="Squad Member 2")
async def mapban(interaction: discord.Interaction, p1: discord.Member = None, p2: discord.Member = None):
    await interaction.response.defer()
    users = load_users()
    target_members = [interaction.user]
    if p1: target_members.append(p1)
    if p2: target_members.append(p2)
    try:
        scraped_dfs = []
        for member in target_members:
            r6_name = users.get(str(member.id), member.display_name)
            df = await fetch_recent_matches(r6_name)
            if not df.empty:
                scraped_dfs.append(df)
        if not scraped_dfs:
            await interaction.edit_original_response(content="❌ Failed to extract match data for any players.")
            return
        squad_df = scraped_dfs[0]
        if len(scraped_dfs) > 1:
            for next_df in scraped_dfs[1:]:
                squad_df = pd.merge(squad_df, next_df, on=['Map', 'Result'], how='inner')
        if squad_df.empty:
            await interaction.edit_original_response(content="❌ **No Shared Matches Found:** You don't have any recent overlapping matches with this squad.")
            return
        map_stats = pd.crosstab(squad_df['Map'], squad_df['Result'])
        if 'Win' not in map_stats.columns: map_stats['Win'] = 0
        if 'Loss' not in map_stats.columns: map_stats['Loss'] = 0
        chart_path = generate_map_chart(map_stats)
        discord_file = discord.File(chart_path, filename="mapban.png")
        title = f"Live Map Analytics for Squad" if len(scraped_dfs) > 1 else f"Live Map Analytics for {target_members[0].display_name}"
        await interaction.edit_original_response(content=f"📊 **{title}** (Found {len(squad_df)} Shared Matches)", attachments=[discord_file])
    except Exception as e:
        await interaction.edit_original_response(content=f"⚠️ **CRITICAL ERROR:** \n`{e}`")

@bot.tree.command(name='carry', description='Calculates the daily squad MVP (Strictly grades Co-op matches).')
@app_commands.describe(p1="Squad Member 1", p2="Squad Member 2", p3="Squad Member 3")
async def carry(interaction: discord.Interaction, p1: discord.Member = None, p2: discord.Member = None, p3: discord.Member = None):
    await interaction.response.defer()
    users = load_users()
    target_members = [interaction.user]
    for p in [p1, p2, p3]:
        if p and p not in target_members:
            target_members.append(p)
    session_start = get_session_start()
    scraped_data = {}
    log_messages = []
    for member in target_members:
        discord_id = str(member.id)
        r6_name = users.get(discord_id, member.display_name)
        df = await fetch_recent_matches(r6_name)
        await asyncio.sleep(2.5)
        if df.empty:
            log_messages.append(f"⚠️ No data found for {r6_name}.")
            continue
        session_matches = df[df['Date'] >= session_start].copy()
        if session_matches.empty:
            log_messages.append(f"💤 {r6_name} hasn't played any matches this session.")
            continue
        session_matches['Match_ID'] = session_matches.groupby(['Map', 'Result']).cumcount()
        scraped_data[r6_name] = session_matches
    if not scraped_data:
        await interaction.edit_original_response(content="**Daily Squad Leaderboard**\nNo matches found for this squad since the 6:00 AM reset!")
        return
    leaderboard_data = []
    if len(scraped_data) == 1:
        solo_player = list(scraped_data.keys())[0]
        df = scraped_data[solo_player]
        kills = int(df['Kills'].sum())
        deaths = int(df['Deaths'].sum())
        matches_played = len(df)
        kd_ratio = round(kills / deaths, 2) if deaths > 0 else float(kills)
        msg = (
            f"🏆 **The Solo Hero Award** 🏆\n"
            f"*Session started at: <t:{int(session_start.timestamp())}:t>*\n\n"
            f"👑 **{solo_player}** is the only one who showed up to the grind today.\n"
            f"> **K/D:** `{kd_ratio}` | **K-D:** {kills} - {deaths} | **Matches:** {matches_played}\n\n"
            f"*Respect the hustle. You dropped this: 👑*"
        )
        leaderboard_data.append({'Player': solo_player, 'KD': kd_ratio, 'Kills': kills, 'Deaths': deaths, 'Matches': matches_played})
        chart_path = generate_carry_chart(leaderboard_data)
        discord_file = discord.File(chart_path, filename="carry_leaderboard.png")
        await interaction.edit_original_response(content=msg, attachments=[discord_file])
        return
    player_names = list(scraped_data.keys())
    shared_matches = scraped_data[player_names[0]][['Map', 'Result', 'Match_ID']]
    for name in player_names[1:]:
        shared_matches = pd.merge(shared_matches, scraped_data[name][['Map', 'Result', 'Match_ID']], on=['Map', 'Result', 'Match_ID'], how='inner')
    if shared_matches.empty:
        await interaction.edit_original_response(content=f"❌ **No Co-op Matches Found!**\nYou all played today, but you didn't play any matches *together* in the same lobby.")
        return
    for r6_name, df in scraped_data.items():
        coop_df = pd.merge(df, shared_matches, on=['Map', 'Result', 'Match_ID'], how='inner')
        total_kills = int(coop_df['Kills'].sum())
        total_deaths = int(coop_df['Deaths'].sum())
        matches_played = len(coop_df)
        kd_ratio = round(total_kills / total_deaths, 2) if total_deaths > 0 else float(total_kills)
        leaderboard_data.append({
            'Player': r6_name,
            'KD': kd_ratio,
            'Kills': total_kills,
            'Deaths': total_deaths,
            'Matches': matches_played
        })
    leaderboard_data.sort(key=lambda x: x['KD'], reverse=True)
    response_msg = f"🏆 **Co-op Squad Leaderboard** 🏆\n*Grading exactly **{len(shared_matches)}** shared matches since 6:00 AM*\n\n"
    medals = ["🥇", "🥈", "🥉", "🥔"]
    for i, p_data in enumerate(leaderboard_data):
        medal = medals[i] if i < len(medals) else "🔹"
        response_msg += (
            f"{medal} **{p_data['Player']}**\n"
            f"> **K/D:** `{p_data['KD']}` | **K-D:** {p_data['Kills']} - {p_data['Deaths']} | **Matches:** {p_data['Matches']}\n\n"
        )
    if log_messages:
        response_msg += "*Logs:*\n" + "\n".join(log_messages)
    chart_path = generate_carry_chart(leaderboard_data)
    discord_file = discord.File(chart_path, filename="carry_leaderboard.png")
    await interaction.edit_original_response(content=response_msg, attachments=[discord_file])

if __name__ == '__main__':
    if not TOKEN or TOKEN == "your_secret_token_goes_here":
        print("CRITICAL ERROR: Discord token is missing.")
    else:
        bot.run(TOKEN)