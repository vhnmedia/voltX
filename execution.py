"""
execution.py - Trade Execution Orchestrator & Trading Partner Simulation

CRITICAL REGULATORY COMPLIANCE NOTE:
- Under CERC regulations, non-licensed entities cannot clear electricity trades.
- This module interfaces with a simulated trading-member partner API.
- For production use, set SIMULATED_EXECUTION=False and configure CERC-registered
  trading-member credentials.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from supabase_client import supabase

SIMULATED_EXECUTION = True

class MockTradingMemberPartnerAPI:
    """Simulates trade placement through a registered Power Exchange Trading Member."""

    @staticmethod
    def submit_order(order_payload: Dict[str, Any]) -> Dict[str, Any]:
        market = order_payload["market_type"]
        bid_price = order_payload["price_inr_per_kwh"]
        clearing_ceiling = order_payload["ceiling_price_inr_per_kwh"]

        # If market conditions spike above ceiling, mock a missed trade
        if bid_price > clearing_ceiling:
            return {
                "status": "missed",
                "cleared_price": None,
                "cleared_quantity_kw": 0,
                "partner_ref": f"SIM-REJ-{uuid.uuid4().hex[:8].upper()}",
                "message": "Market Clearing Price exceeded bid ceiling. Order was unexecuted."
            }

        return {
            "status": "cleared",
            "cleared_price": round(bid_price * 0.985, 3),  # Typical marginal discount
            "cleared_quantity_kw": order_payload["quantity_kw"],
            "partner_ref": f"SIM-CLR-{uuid.uuid4().hex[:8].upper()}",
            "message": "Trade matched and cleared on simulated IEX book."
        }


class ExecutionOrchestrator:
    @classmethod
    def execute_plan_bids(cls, plan_id: str, facility_id: str, plan_date: str, block_allocations: List[Dict[str, Any]], ceiling_price: float) -> List[Dict[str, Any]]:
        logs = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for alloc in block_allocations:
            b_id = alloc["block_id"]
            
            # Path 1: DISCOM Fallback (Logged as procurement decision, not an exchange order)
            if alloc.get("is_fallback") or alloc["discom_allocation_kw"] > 0:
                record = {
                    "plan_id": plan_id,
                    "facility_id": facility_id,
                    "trade_date": plan_date,
                    "block_id": b_id,
                    "market_type": "DISCOM",
                    "submitted_at": now_iso,
                    "price_inr_per_kwh": None,
                    "ceiling_price_inr_per_kwh": ceiling_price,
                    "quantity_kw": alloc["discom_allocation_kw"],
                    "cleared_price": None,
                    "cleared_quantity_kw": alloc["discom_allocation_kw"],
                    "status": "discom_fallback",
                    "is_simulated": True,
                    "mock_partner_ref": "DISCOM-SAFETY-VALVE"
                }
                logs.append(record)

            # Path 2: DAM Order
            if alloc["dam_allocation_kw"] > 0:
                dam_order = {
                    "market_type": "DAM",
                    "price_inr_per_kwh": ceiling_price,
                    "ceiling_price_inr_per_kwh": ceiling_price,
                    "quantity_kw": alloc["dam_allocation_kw"]
                }
                res = MockTradingMemberPartnerAPI.submit_order(dam_order)
                logs.append({
                    "plan_id": plan_id,
                    "facility_id": facility_id,
                    "trade_date": plan_date,
                    "block_id": b_id,
                    "market_type": "DAM",
                    "submitted_at": now_iso,
                    "price_inr_per_kwh": ceiling_price,
                    "ceiling_price_inr_per_kwh": ceiling_price,
                    "quantity_kw": alloc["dam_allocation_kw"],
                    "cleared_price": res["cleared_price"],
                    "cleared_quantity_kw": res["cleared_quantity_kw"],
                    "status": res["status"],
                    "is_simulated": True,
                    "mock_partner_ref": res["partner_ref"],
                    "error_message": res.get("message")
                })

            # Path 3: RTM Order
            if alloc["rtm_allocation_kw"] > 0:
                rtm_order = {
                    "market_type": "RTM",
                    "price_inr_per_kwh": ceiling_price,
                    "ceiling_price_inr_per_kwh": ceiling_price,
                    "quantity_kw": alloc["rtm_allocation_kw"]
                }
                res = MockTradingMemberPartnerAPI.submit_order(rtm_order)
                logs.append({
                    "plan_id": plan_id,
                    "facility_id": facility_id,
                    "trade_date": plan_date,
                    "block_id": b_id,
                    "market_type": "RTM",
                    "submitted_at": now_iso,
                    "price_inr_per_kwh": ceiling_price,
                    "ceiling_price_inr_per_kwh": ceiling_price,
                    "quantity_kw": alloc["rtm_allocation_kw"],
                    "cleared_price": res["cleared_price"],
                    "cleared_quantity_kw": res["cleared_quantity_kw"],
                    "status": res["status"],
                    "is_simulated": True,
                    "mock_partner_ref": res["partner_ref"],
                    "error_message": res.get("message")
                })

        # Batch insert to trade_logs
        if logs:
            supabase.table("trade_logs").insert(logs).execute()

        return logs
