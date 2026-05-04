# 🎯 R6 Squad Analyzer Bot (V3.0)

A professional-grade Discord bot built to track, aggregate, and visualize Rainbow Six Siege squad telemetry in real-time. 

## 🚀 V3.0 Architecture Upgrades
* **Live Network Fetching:** Integrated `siegeapi` to bypass Ubisoft's lack of a public API, allowing for secure, real-time ranked telemetry extraction.
* **Persistent Memory Bank:** Replaced static JSON storage with a fully integrated **SQLite** relational database, utilizing `pandas.pivot_table()` to safely aggregate daily MMR snapshots.
* **Optimistic Fallback:** Engineered a dual-path data pipeline. If Ubisoft's servers rate-limit the bot (HTTP 429), it gracefully falls back to the local SQLite database to ensure zero downtime.
* **Data Science Engine:** Utilizes cross-tabulation math to normalize and calculate the highest win-rate Operator synergies and Map ban priorities.
* **Dynamic Visualization:** Leverages `matplotlib` and `seaborn` to generate clean, Apple-style UI charts dynamically scaled to the squad's exact MMR spread.

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **Core:** `discord.py`, `sqlite3`
* **Network:** `siegeapi`, `aiohttp`
* **Data Science:** `pandas`, `numpy`
* **Visualization:** `matplotlib`, `seaborn`

## ⚙️ How to Run Locally
1. Clone the repository.
2. Run `pip install -r requirements.txt`.
3. Create a `.env` file in the root directory with `DISCORD_TOKEN`, `UBISOFT_EMAIL`, and `UBISOFT_PASSWORD`.
4. Run `python src/main.py`.