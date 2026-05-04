import os
import logging
from typing import Optional
from siegeapi import Auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_player_data(player_name: str) -> Optional[dict]:
    """Fetches live Ranked 2.0 telemetry for a given player using siegeapi."""
    email = os.getenv("UBISOFT_EMAIL")
    password = os.getenv("UBISOFT_PASSWORD")
    
    if not email or not password:
        logger.error("API ABORTED: Missing Ubisoft credentials in .env file.")
        return None

    # Instantiate Auth outside the try block so 'finally' can always access it
    auth = Auth(email, password)
    
    try:
        player = await auth.get_player(name=player_name)
        await player.load_ranked_v2()
        
        current_mmr = player.ranked_profile.rank_points
        current_rank = player.ranked_profile.rank
        
        live_data = {
            "name": player.name,
            "current_mmr": current_mmr,
            "rank": current_rank
        }
        
        logger.info(f"API Success: Fetched live MMR ({current_mmr}) for {player_name}")
        return live_data
        
    except Exception as e:
        logger.error(f"API Error fetching {player_name}: {e}")
        return None
        
    finally:
        # This guarantees the connection closes, preventing memory leaks, even if the API throws an error
        await auth.close()