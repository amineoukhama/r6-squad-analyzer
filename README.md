# R6 Siege Squad Analyzer

An automated data pipeline and Discord integration for Rainbow Six Siege telemetry. This tool processes raw match data to deliver automated rank tracking, map win rates, and operator synergy analytics directly to end-users via Discord.

## Core Features
* **MMR Timeline Tracking:** Visualizes player rank points over time to identify performance trends and win/loss streaks.
* **Objective Map Analytics:** Aggregates map-specific win rates to mathematically guide the pre-match ban phase.
* **Operator Synergy:** Cross-references pick data to identify high-win-rate operator combinations.

## Architecture & Tech Stack
* **Language:** Python 3
* **Data Processing:** Pandas
* **Visualization:** Matplotlib / Seaborn (Minimalist styling)
* **Delivery:** Discord.py

## Project Status
*Currently in active development.*