"""
reconciliation.py - Savings & CO2 Post-Delivery Reconciliation Service

METHODOLOGY NOTICE:
- The CO2 intensity numbers used here are estimated grid proxies based on CEA
  (Central Electricity Authority) baseline emission factors (average ~0.72 kg CO2/kWh).
- Time-of-day adjustments (Blocks 36-68: 09:00 - 17:00 IST) approximate solar
  displacement (0.45 kg CO2/kWh) vs peak thermal blocks (0.82 kg CO2/kWh).
- This is an operational heuristic, NOT a certified third-party carbon audit.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from supabase_client import supabase

SOLAR_HOURS_CO2_FACTOR = 0.45    # kg CO2/kWh during high renewable window (09:00 - 17:00)
THERMAL_BASE_CO2_FACTOR = 0.82   # kg CO2/kWh during evening/night peak
FLAT_DISCOM_CO2_FACTOR = 0.72    # Average grid emission factor

class ReconciliationService:
    @staticmethod
    def generate_monthly_reconciliation(facility_id: str, report_month: str) -> Dict[str, Any]:
        # Fetch facility details
        fac = supabase.table("facilities").select("*").eq("id", facility_id).single().execute().data
        discom_tariff = float(fac.get("discom_tariff_inr_per_kwh", 8.50))

        # Query executed trade logs
        trades = supabase.table("trade_logs").select("*").eq("facility_id", facility_id).execute().data

        total_exchange_kwh = 0.0
        total_discom_kwh = 0.0
        actual_exchange_cost = 0.0
        actual_co2_kg = 0.0

        for t in trades:
            qty_kwh = (t.get("cleared_quantity_kw") or t.get("quantity_kw") or 0.0) * 0.25
            block = t.get("block_id", 1)
            
            # Solar-rich block detection: Blocks 36 to 68 correspond to 09:00 - 17:00
            is_solar_window = (36 <= block <= 68)
            block_factor = SOLAR_HOURS_CO2_FACTOR if is_solar_window else THERMAL_BASE_CO2_FACTOR

            if t.get("status") == "cleared":
                total_exchange_kwh += qty_kwh
                # Cleared price + open access surcharge proxy
                unit_price = float(t.get("cleared_price") or 4.50) + 2.45
                actual_exchange_cost += qty_kwh * unit_price
                actual_co2_kg += qty_kwh * block_factor
            else:
                total_discom_kwh += qty_kwh
                actual_co2_kg += qty_kwh * FLAT_DISCOM_CO2_FACTOR

        total_kwh = total_exchange_kwh + total_discom_kwh
        discom_actual_cost = total_discom_kwh * discom_tariff
        total_actual_cost = actual_exchange_cost + discom_actual_cost

        # Counterfactual 1: 100% DISCOM purchase
        counterfactual_discom_cost = total_kwh * discom_tariff
        baseline_co2_kg = total_kwh * FLAT_DISCOM_CO2_FACTOR

        # Counterfactual 2: Blind DAM-only purchase
        dam_blind_rate = 5.20 + 2.45  # Baseline DAM average price + surcharge
        counterfactual_dam_only_cost = (total_kwh * dam_blind_rate)

        savings_vs_discom = max(0.0, counterfactual_discom_cost - total_actual_cost)
        savings_vs_dam_only = counterfactual_dam_only_cost - total_actual_cost
        savings_pct = (savings_vs_discom / counterfactual_discom_cost * 100) if counterfactual_discom_cost > 0 else 0.0
        co2_avoided_kg = max(0.0, baseline_co2_kg - actual_co2_kg)

        record = {
            "facility_id": facility_id,
            "report_month": report_month,
            "total_consumption_kwh": round(total_kwh, 2),
            "exchange_kwh": round(total_exchange_kwh, 2),
            "discom_kwh": round(total_discom_kwh, 2),
            "actual_cost_inr": round(total_actual_cost, 2),
            "discom_baseline_cost_inr": round(counterfactual_discom_cost, 2),
            "dam_only_baseline_cost_inr": round(counterfactual_dam_only_cost, 2),
            "savings_vs_discom_inr": round(savings_vs_discom, 2),
            "savings_vs_dam_only_inr": round(savings_vs_dam_only, 2),
            "savings_pct": round(savings_pct, 2),
            "co2_exchange_kg": round(actual_co2_kg, 2),
            "co2_discom_baseline_kg": round(baseline_co2_kg, 2),
            "co2_avoided_kg": round(co2_avoided_kg, 2),
            "report_generated_at": datetime.now(timezone.utc).isoformat()
        }

        supabase.table("monthly_reconciliation").upsert(record).execute()
        return record
