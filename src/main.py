import os
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv

# FIXED: Added load_match_data back so the mapban command functions properly
from data_processor import load_match_data, load_match_data_from_db, get_map_stats, get_synergy_stats
from visualizer import generate_mmr_chart, generate_map_chart, generate_synergy_chart
from api_client import fetch_player_data
from db_manager import init_db, log_mmr

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
    """Links a Discord account to an R6 player name in the database."""
    discord_id = str(ctx.author.id)
    users = load_users()
    users[discord_id] = r6_name
    save_users(users)
    await ctx.send(f"✅ **Registration Complete:** Your Discord is now linked to R6 Player: `{r6_name}`")

@bot.command(name='rank')
async def rank(ctx, *members: discord.Member):
    """Generates an MMR timeline with Optimistic Network Fetching."""
    users = load_users()
    target_members = members if members else [ctx.author]
    players_to_graph = []
    
    status_msg = await ctx.send("⏳ *Querying Ubisoft Network for telemetry...*")
    live_data_found = False

    for member in target_members:
        discord_id = str(member.id)
        r6_name = users.get(discord_id, member.display_name)
        
        live_data = await fetch_player_data(r6_name)
        
        if live_data:
            mmr = live_data["current_mmr"]
            rank_name = live_data["rank"]
            
            log_mmr(r6_name, mmr, rank_name)
            
            await ctx.send(f"📡 **Live Network Stats for {r6_name}:**\nRank: **{rank_name}** | MMR: **{mmr}**\n*(Snapshot saved to database)*")
            live_data_found = True
        else:
            players_to_graph.append(r6_name)

    if not players_to_graph:
        await status_msg.delete()
        if not live_data_found:
            await ctx.send("❌ **Error:** No valid telemetry found on Network or Local DB.")
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
        await ctx.send(content="**Squad MMR Timeline (Local Fallback)**", file=discord_file)
        await status_msg.delete()
        
    except Exception as e:
        await ctx.send(f"⚠️ **CRITICAL ERROR:** Failed to process telemetry.\n`{e}`")

@bot.command(name='mapban')
async def mapban(ctx):
    status_msg = await ctx.send("⏳ *Aggregating map statistics...*")
    try:
        df = load_match_data('data/sample_match_data.json')
        map_analytics = get_map_stats(df)
        chart_path = generate_map_chart(map_analytics)
        discord_file = discord.File(chart_path, filename="map_win_rates.png")
        await ctx.send(content="**Map Analytics: Objective Ban Guide**", file=discord_file)
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