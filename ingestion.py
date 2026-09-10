"""
GreenWatt — Data Ingestion & Processing Pipeline
Scheduled jobs for three feeds:
  a) IEX market data (DAM + RTM)
  b) Weather API (solar, wind, temperature)
  c) Facility meters (15-min consumption)

NOTE: In production, each job should be a Celery beat task with proper retry logic.
For the hackathon, we expose each as an async function callable by APScheduler.
"""
import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
import httpx
import random
import math
from supabase import Client

from app.core.config import get_settings
from app.db.supabase_client import get_supabase_service

logger = logging.getLogger(__name__)
settings = get_settings()

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS: Data generators (SIMULATION for hackathon)
# In production, replace these with real API calls.
# ─────────────────────────────────────────────────────────────────────────────

def _simulate_dam_prices(trade_date: date) -> List[Dict]:
    """
    SIMULATED: Generates realistic-ish DAM MCP data for 96 blocks.
    Real data: fetch from IEX API GET /market-data/dam/clearing-prices
    Typical IEX DAM range: INR 2.5–8.0/kWh with peaks around block 40-52 (morning),
    75-88 (evening), and troughs around block 1-20 (night).
    """
    blocks = []
    base_dt = datetime.combine(trade_date, datetime.min.time())

    for block in range(1, 97):
        hour = (block - 1) * 0.25  # each block = 15 minutes
        # Simulate typical India demand curve: two peaks (morning + evening)
        morning_peak = 5 * math.exp(-0.5 * ((hour - 10) / 2) ** 2)
        evening_peak = 7 * math.exp(-0.5 * ((hour - 20) / 1.5) ** 2)
        base_price = 3.0 + morning_peak + evening_peak
        # Add noise
        noise = random.gauss(0, 0.3)
        mcp = max(1.5, round(base_price + noise, 4))
        volume = round(random.uniform(2000, 8000), 2)  # MWh

        ts = base_dt + timedelta(minutes=15 * (block - 1))
        blocks.append({
            "timestamp": ts.isoformat(),
            "market_type": "DAM",
            "block_id": block,
            "mcp_price": mcp,
            "volume_mwh": volume,
            "region": "India",
            "source": "IEX_SIMULATED",
        })
    return blocks


def _simulate_rtm_prices(trade_date: date) -> List[Dict]:
    """
    SIMULATED: Generates RTM data for 48 sessions (30-min intervals).
    RTM tends to be more volatile than DAM, with occasional price dips
    when solar peaks (midday) or demand drops.
    """
    sessions = []
    base_dt = datetime.combine(trade_date, datetime.min.time())

    for session in range(1, 49):
        hour = (session - 1) * 0.5
        solar_dip = 2.5 * math.exp(-0.5 * ((hour - 13) / 2) ** 2)  # midday solar
        base_price = 4.0 - solar_dip + random.gauss(0, 0.5)
        mcp = max(1.0, round(base_price, 4))
        volume = round(random.uniform(500, 3000), 2)

        ts = base_dt + timedelta(minutes=30 * (session - 1))
        sessions.append({
            "timestamp": ts.isoformat(),
            "market_type": "RTM",
            "block_id": session,
            "mcp_price": mcp,
            "volume_mwh": volume,
            "region": "India",
            "source": "IEX_SIMULATED",
        })
    return sessions


def _simulate_weather(trade_date: date, region: str) -> List[Dict]:
    """
    SIMULATED: Hourly weather data.
    Production: call Open-Meteo or IMD API.
    """
    records = []
    base_dt = datetime.combine(trade_date, datetime.min.time())

    for hour in range(24):
        solar = max(0, 800 * math.sin(math.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0
        solar += random.gauss(0, 30)
        wind = max(0, random.gauss(8, 3))
        temp = 25 + 10 * math.sin(math.pi * (hour - 6) / 12) + random.gauss(0, 2)

        ts = base_dt + timedelta(hours=hour)
        records.append({
            "timestamp": ts.isoformat(),
            "region": region,
            "solar_irradiance": round(max(0, solar), 2),
            "wind_speed": round(wind, 2),
            "temperature": round(temp, 2),
            "cloud_cover": round(random.uniform(0, 60), 2),
            "source": "OPENMETEO_SIMULATED",
        })
    return records


def _simulate_facility_load(facility_id: str, trade_date: date) -> List[Dict]:
    """
    SIMULATED: 15-min interval consumption data for a facility.
    Production: pull from smart meter API or DISCOM portal.
    """
    records = []
    base_dt = datetime.combine(trade_date, datetime.min.time())

    # Base demand varies by facility type; using random seed from facility_id for consistency
    seed = int(facility_id.replace("-", "")[:8], 16) % 1000
    rng = random.Random(seed)
    base_kw = rng.uniform(200, 2000)

    for block in range(96):
        hour = block * 0.25
        # Office-style load curve
        work_hours = max(0, math.sin(math.pi * (hour - 8) / 10)) if 8 <= hour <= 20 else 0.1
        consumption = base_kw * (0.3 + 0.7 * work_hours) + random.gauss(0, base_kw * 0.05)
        ts = base_dt + timedelta(minutes=15 * block)

        records.append({
            "timestamp": ts.isoformat(),
            "facility_id": facility_id,
            "consumption_kw": round(max(0, consumption), 2),
            "source": "METER_SIMULATED",
        })
    return records


# ─────────────────────────────────────────────────────────────────────────────
# JOB A: Ingest IEX market data
# ─────────────────────────────────────────────────────────────────────────────

async def ingest_market_data(trade_date: Optional[date] = None):
    """
    Scheduled: Run once after DAM clearing (typically 12:30 IST) and
    continuously for RTM every 30 minutes.
    """
    if trade_date is None:
        trade_date = date.today()

    client: Client = get_supabase_service()

    logger.info(f"[Ingestion] Starting market data for {trade_date}")

    try:
        dam_records = _simulate_dam_prices(trade_date)
        rtm_records = _simulate_rtm_prices(trade_date)

        # Upsert to avoid duplicates on re-run
        all_records = dam_records + rtm_records
        # Batch upsert in chunks of 500
        for i in range(0, len(all_records), 500):
            batch = all_records[i:i + 500]
            client.table("market_prices").upsert(batch).execute()

        logger.info(f"[Ingestion] Market data: {len(dam_records)} DAM + {len(rtm_records)} RTM blocks ingested")
        return {"dam": len(dam_records), "rtm": len(rtm_records)}

    except Exception as e:
        logger.error(f"[Ingestion] Market data failed: {e}")
        raise


# ─────────────────────────────────────────────────────────────────────────────
# JOB B: Ingest weather data
# ─────────────────────────────────────────────────────────────────────────────

async def ingest_weather_data(trade_date: Optional[date] = None):
    """Scheduled: Run every 6 hours."""
    if trade_date is None:
        trade_date = date.today()

    client: Client = get_supabase_service()
    regions = ["Maharashtra", "Gujarat", "Tamil Nadu", "Karnataka"]

    logger.info(f"[Ingestion] Starting weather data for {trade_date}")

    total = 0
    for region in regions:
        records = _simulate_weather(trade_date, region)
        client.table("weather_data").upsert(records).execute()
        total += len(records)

    logger.info(f"[Ingestion] Weather: {total} records across {len(regions)} regions")
    return {"records": total}


# ─────────────────────────────────────────────────────────────────────────────
# JOB C: Ingest facility meter data
# ─────────────────────────────────────────────────────────────────────────────

async def ingest_facility_loads(trade_date: Optional[date] = None):
    """Scheduled: Run every 15 minutes (near real-time meter polling)."""
    if trade_date is None:
        trade_date = date.today()

    client: Client = get_supabase_service()

    # Fetch all active facilities
    result = client.table("facilities").select("id").eq("is_active", True).execute()
    facilities = result.data or []

    logger.info(f"[Ingestion] Starting load data for {len(facilities)} facilities")

    total = 0
    for fac in facilities:
        records = _simulate_facility_load(fac["id"], trade_date)
        client.table("facility_load").upsert(records).execute()
        total += len(records)

    logger.info(f"[Ingestion] Load: {total} records for {len(facilities)} facilities")
    return {"facilities": len(facilities), "records": total}


# ─────────────────────────────────────────────────────────────────────────────
# MASTER RUNNER (used by scheduler or manual trigger)
# ─────────────────────────────────────────────────────────────────────────────

async def run_full_ingestion(trade_date: Optional[date] = None):
    """Run all three ingestion jobs."""
    results = {}
    results["market"] = await ingest_market_data(trade_date)
    results["weather"] = await ingest_weather_data(trade_date)
    results["loads"] = await ingest_facility_loads(trade_date)
    return results
