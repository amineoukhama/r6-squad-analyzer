import os
import json
import discord
import pandas as pd
from discord.ext import commands
from dotenv import load_dotenv

from data_processor import load_match_data_from_db, get_synergy_stats
from visualizer import generate_mmr_chart, generate_map_chart, generate_synergy_chart
from db_manager import init_db, log_mmr
from tracker_scraper import fetch_recent_matches

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

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

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send(f'Pong! 🏓 Gateway latency: {round(bot.latency * 1000)}ms.')

@bot.command(name='register')
async def register(ctx, r6_name: str):
    discord_id = str(ctx.author.id)
    users = load_users()
    users[discord_id] = r6_name
    save_users(users)
    await ctx.send(f"✅ **Registration Complete:** Your Discord is now linked to R6 Player: `{r6_name}`")

@bot.command(name='rank')
async def rank(ctx, *members: discord.Member):
    users = load_users()
    target_members = members if members else [ctx.author]
    players_to_graph = []
    
    status_msg = await ctx.send("🕵️‍♂️ *Deploying Ghost Browser for MMR Telemetry...*")
    live_data_found = False

    for member in target_members:
        discord_id = str(member.id)
        r6_name = users.get(discord_id, member.display_name)
        
        df_matches = await fetch_recent_matches(r6_name)
        
        if not df_matches.empty and 'RP' in df_matches.columns:
            mmr = int(df_matches.iloc[0]['RP'])
            rank_name = "Ranked (Scraped)"
            
            log_mmr(r6_name, mmr, rank_name)
            
            await ctx.send(f"📡 **Live Scraped Stats for {r6_name}:**\nMMR: **{mmr}**\n*(Snapshot saved to database)*")
            live_data_found = True
        else:
            players_to_graph.append(r6_name)

    if not players_to_graph:
        await status_msg.delete()
        if not live_data_found:
            await ctx.send("❌ **Error:** Scraper failed to extract RP. R6Tracker may be blocking the request.")
        return

    try:
        df = load_match_data_from_db()
        valid_columns = ['date']
        
        for player in players_to_graph:
            if player in df.columns:
                valid_columns.append(player)
            else:
                await ctx.send(f"⚠️ **Notice:** No local match data found for `{player}`. Type `!register <R6_Name>` to fix.")
                
        if len(valid_columns) == 1:
            return await status_msg.edit(content="❌ **Error:** Aborting render. No valid data columns found.")
            
        filtered_df = df[valid_columns]
        chart_path = generate_mmr_chart(filtered_df)
        
        discord_file = discord.File(chart_path, filename="mmr_timeline.png")
        await ctx.send(content="**Squad MMR Timeline (Local Database)**", file=discord_file)
        await status_msg.delete()
        
    except Exception as e:
        await ctx.send(f"⚠️ **CRITICAL ERROR:** Failed to process telemetry.\n`{e}`")

@bot.command(name='mapban')
async def mapban(ctx, r6_name: str = None):
    if not r6_name:
        users = load_users()
        r6_name = users.get(str(ctx.author.id))
        if not r6_name:
            await ctx.send("⚠️ You aren't registered! Type `!register <R6_Name>` or use `!mapban <R6_Name>`.")
            return

    status_msg = await ctx.send(f"🕵️‍♂️ *Deploying Ghost Browser... scraping live match history for **{r6_name}**...*")
    
    try:
        df = await fetch_recent_matches(r6_name)
        
        if df.empty:
            await status_msg.edit(content=f"❌ Failed to extract match data for {r6_name}.")
            return

        map_stats = pd.crosstab(df['Map'], df['Result'])
        
        if 'Win' not in map_stats.columns:
            map_stats['Win'] = 0
        if 'Loss' not in map_stats.columns:
            map_stats['Loss'] = 0

        chart_path = generate_map_chart(map_stats)
        discord_file = discord.File(chart_path, filename="mapban.png")
        
        await ctx.send(content=f"📊 **Live Map Analytics for {r6_name}** (Last {len(df)} Matches)", file=discord_file)
        await status_msg.delete()
        
    except Exception as e:
        await ctx.send(f"⚠️ **CRITICAL ERROR:** Failed to process map analytics.\n`{e}`")

@bot.command(name='synergy')
async def synergy(ctx):
    status_msg = await ctx.send("⏳ *Running Data Science Synergy Engine...*")
    try:
        synergy_analytics = get_synergy_stats('data/synergy_data.json')
        chart_path = generate_synergy_chart(synergy_analytics)
        discord_file = discord.File(chart_path, filename="synergy_win_rates.png")
        await ctx.send(content="**Data Science: Operator Synergy Ratings**", file=discord_file)
        await status_msg.delete()
    except Exception as e:
        await ctx.send(f"⚠️ **CRITICAL ERROR:** Failed to process synergy analytics.\n`{e}`")

if __name__ == '__main__':
    if not TOKEN or TOKEN == "your_secret_token_goes_here":
        print("CRITICAL ERROR: Discord token is missing.")
    else:
        bot.run(TOKEN)