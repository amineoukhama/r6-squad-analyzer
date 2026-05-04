import asyncio
import pandas as pd
from playwright.async_api import async_playwright

async def fetch_recent_matches(username: str) -> pd.DataFrame:
    """Invisibly scrapes R6Tracker for recent match data."""
    async with async_playwright() as p:
        # headless=True makes the browser completely invisible
        browser = await p.chromium.launch(headless=True, slow_mo=50)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        target_url = f"https://r6.tracker.network/r6siege/profile/ubi/{username}/matches"
        
        try:
            await page.goto(target_url, timeout=60000)
            
            # Silently handle cookies
            try:
                accept_btn = page.get_by_role("button", name="Accept", exact=True).first
                await accept_btn.wait_for(state="visible", timeout=4000)
                await accept_btn.click()
                await asyncio.sleep(1)
                
                accept_all_btn = page.get_by_role("button", name="Accept All", exact=True).first
                if await accept_all_btn.is_visible():
                    await accept_all_btn.click()
            except Exception:
                pass # Proceed if no banner appears

            # Extract the data
            await page.wait_for_selector("div.v3-match-row", state="visible", timeout=15000)
            match_elements = await page.locator("div.v3-match-row").all()
            
            parsed_matches = []
            
            for row in match_elements:
                row_text = await row.inner_text()
                data = [line.strip() for line in row_text.split('\n') if line.strip()]
                
                try:
                    raw_map_str = data[0]
                    map_name = raw_map_str.split("ago")[-1].strip() if "ago" in raw_map_str else raw_map_str
                    
                    score_idx = data.index("Score")
                    team_a = int(data[score_idx + 1])
                    team_b = int(data[score_idx + 3])
                    result = "Win" if team_a > team_b else "Loss"
                    
                    rp_idx = data.index("RP")
                    absolute_rp = int(data[rp_idx + 1].replace(',', '')) # Converts "1,801" to 1801
                    
                    parsed_matches.append({
                        "Map": map_name,
                        "Result": result,
                        "RP": absolute_rp
                    })
                except ValueError:
                    continue
                    
            await browser.close()
            return pd.DataFrame(parsed_matches)
            
        except Exception as e:
            print(f"Scraper Error for {username}: {e}")
            await browser.close()
            return pd.DataFrame() # Return an empty DataFrame if it fails so the bot doesn't crash