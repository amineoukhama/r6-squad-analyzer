import asyncio
import re
from datetime import datetime, timedelta
import pandas as pd
from playwright.async_api import async_playwright

def parse_time_ago(time_str: str) -> datetime:
    now = datetime.now()
    time_str = time_str.lower().strip()
    
    if "yesterday" in time_str:
        return now - timedelta(days=1)
        
    match = re.search(r'(\d+)', time_str)
    if not match:
        return now - timedelta(days=365)
        
    amount = int(match.group(1))
    
    if "s" in time_str and "sec" not in time_str and "score" not in time_str: return now - timedelta(seconds=amount)
    if "m" in time_str and "min" not in time_str: return now - timedelta(minutes=amount)
    if "h" in time_str and "hour" not in time_str: return now - timedelta(hours=amount)
    if "d" in time_str and "day" not in time_str: return now - timedelta(days=amount)
    if "w" in time_str and "week" not in time_str: return now - timedelta(weeks=amount)
    
    if "sec" in time_str: return now - timedelta(seconds=amount)
    if "min" in time_str: return now - timedelta(minutes=amount)
    if "hour" in time_str: return now - timedelta(hours=amount)
    if "day" in time_str: return now - timedelta(days=amount)
    if "week" in time_str: return now - timedelta(weeks=amount)
    if "month" in time_str: return now - timedelta(days=amount * 30)
    if "year" in time_str: return now - timedelta(days=amount * 365)
        
    return now - timedelta(days=365)

async def fetch_recent_matches(username: str) -> pd.DataFrame:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=50)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        target_url = f"https://r6.tracker.network/r6siege/profile/ubi/{username}/matches"
        
        try:
            await page.goto(target_url, timeout=60000)
            
            try:
                accept_btn = page.get_by_role("button", name="Accept", exact=True).first
                await accept_btn.wait_for(state="visible", timeout=4000)
                await accept_btn.click()
                await asyncio.sleep(1)
                accept_all_btn = page.get_by_role("button", name="Accept All", exact=True).first
                if await accept_all_btn.is_visible():
                    await accept_all_btn.click()
            except Exception:
                pass
                
            await page.wait_for_selector("div.v3-match-row", state="visible", timeout=15000)
            match_elements = await page.locator("div.v3-match-row").all()
            parsed_matches = []
            
            for row in match_elements:
                row_text = await row.inner_text()
                data = [line.strip() for line in row_text.split('\n') if line.strip()]
                
                try:
                    raw_map_str = data[0]
                    date_obj = datetime.now() - timedelta(days=365)
                    map_name = raw_map_str
                    
                    if "ago" in raw_map_str.lower():
                        parts = raw_map_str.lower().split("ago")
                        time_str = parts[0] + "ago"
                        date_obj = parse_time_ago(time_str)
                        map_name = raw_map_str[len(time_str):].strip()
                    else:
                        for item in data[:5]:
                            item_lower = item.lower()
                            if "yesterday" in item_lower:
                                date_obj = parse_time_ago(item)
                                break
                            elif " jan " in item_lower or " feb " in item_lower or " mar " in item_lower or " apr " in item_lower or " may " in item_lower or " jun " in item_lower or " jul " in item_lower or " aug " in item_lower or " sep " in item_lower or " oct " in item_lower or " nov " in item_lower or " dec " in item_lower:
                                break
                                
                    score_idx = data.index("Score")
                    team_a = int(data[score_idx + 1])
                    team_b = int(data[score_idx + 3])
                    result = "Win" if team_a > team_b else "Loss"
                    
                    rp_idx = data.index("RP")
                    absolute_rp = int(data[rp_idx + 1].replace(',', ''))
                    
                    kills, deaths = 0, 0
                    if "K/D/A" in data:
                        kda_idx = data.index("K/D/A")
                        kills = int(data[kda_idx + 1].strip())
                        deaths = int(data[kda_idx + 2].strip())

                    parsed_matches.append({
                        "Map": map_name.title(),
                        "Date": date_obj,
                        "Result": result,
                        "RP": absolute_rp,
                        "Kills": kills,
                        "Deaths": deaths
                    })
                except (ValueError, IndexError):
                    continue
                    
            await browser.close()
            return pd.DataFrame(parsed_matches)
            
        except Exception as e:
            print(f"Scraper Error for {username}: {e}")
            await browser.close()
            return pd.DataFrame()