import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# --- Import ALL our custom data and visualization functions ---
from data_processor import load_match_data, get_map_stats
from visualizer import generate_mmr_chart, generate_map_chart

# 1. SECURITY
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 2. CONFIGURATION
intents = discord.Intents.default()
intents.message_content = True

# 3. INITIALIZATION
bot = commands.Bot(command_prefix='!', intents=intents)

# 4. EVENT LISTENER: Startup
@bot.event
async def on_ready():
    print(f'System Online: Logged in securely as {bot.user.name}')
    print('-----------------------------------------')
    print('Awaiting command inputs...')

# 5. COMMAND: Network Ping Test
@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! 🏓 Gateway latency: {latency}ms.')

# 6. COMMAND: Rank Tracker
@bot.command(name='rank')
async def rank(ctx):
    """Generates and sends the user's MMR timeline chart."""
    status_msg = await ctx.send("⏳ *Fetching telemetry and rendering timeline...*")
    try:
        target_file = 'data/sample_match_data.json'
        df = load_match_data(target_file)
        chart_path = generate_mmr_chart(df)
        
        discord_file = discord.File(chart_path, filename="mmr_timeline.png")
        await ctx.send(content="**MMR Timeline Analytics**", file=discord_file)
        await status_msg.delete()
    except Exception as e:
        await ctx.send(f"⚠️ **CRITICAL ERROR:** Failed to process telemetry.\n`{e}`")

# 7. COMMAND: Map Ban Analytics
@bot.command(name='mapban')
async def mapban(ctx):
    """Generates and sends the map win rate analytics for the ban phase."""
    status_msg = await ctx.send("⏳ *Aggregating map statistics...*")
    try:
        target_file = 'data/sample_match_data.json'
        
        # A. Pipeline Execution
        df = load_match_data(target_file)
        map_analytics = get_map_stats(df)
        chart_path = generate_map_chart(map_analytics)
        
        # B. Delivery
        discord_file = discord.File(chart_path, filename="map_win_rates.png")
        await ctx.send(content="**Map Analytics: Objective Ban Guide**", file=discord_file)
        await status_msg.delete()
    except Exception as e:
        await ctx.send(f"⚠️ **CRITICAL ERROR:** Failed to process map analytics.\n`{e}`")

# 8. EXECUTION
if __name__ == '__main__':
    if not TOKEN or TOKEN == "your_secret_token_goes_here":
        print("CRITICAL ERROR: Discord token is missing.")
    else:
        bot.run(TOKEN)