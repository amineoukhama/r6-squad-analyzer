import os
import json
import discord
import pandas as pd
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from data_processor import load_match_data_from_db, get_synergy_stats
from visualizer import generate_mmr_chart, generate_map_chart, generate_synergy_chart
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

@bot.tree.command(name='synergy', description='View Data Science Operator Synergy Ratings.')
async def synergy(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        synergy_analytics = get_synergy_stats('data/synergy_data.json')
        chart_path = generate_synergy_chart(synergy_analytics)
        discord_file = discord.File(chart_path, filename="synergy_win_rates.png")
        await interaction.edit_original_response(content="**Data Science: Operator Synergy Ratings**", attachments=[discord_file])
    except Exception as e:
        await interaction.edit_original_response(content=f"⚠️ **CRITICAL ERROR:** \n`{e}`")

if __name__ == '__main__':
    if not TOKEN or TOKEN == "your_secret_token_goes_here":
        print("CRITICAL ERROR: Discord token is missing.")
    else:
        bot.run(TOKEN)