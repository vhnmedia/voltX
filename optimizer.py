"""
optimizer.py - Linear Programming Procurement Optimizer

Mathematical Formulation:
Minimize Total Cost:
  Sum_{b in Window} [
      (Price_DAM_est[b] * P_DAM[b]) +
      (Price_RTM_est[b] * P_RTM[b]) +
      (Tariff_DISCOM * P_DISCOM[b])
  ]
Subject to:
  P_DAM[b] + P_RTM[b] + P_DISCOM[b] = Required_Load[b]  for all blocks b
  P_RTM[b] <= Alpha_Risk * Max_RTM_Allocation
  If DAM and RTM forecasts exceed Ceiling_Price -> P_DISCOM[b] = Required_Load[b]
"""

import pulp
from typing import List, Dict, Any

class PowerProcurementOptimizer:
    @staticmethod
    def run_optimization(
        plan_date: str,
        facility_id: str,
        discom_tariff_inr: float,
        ceiling_price_inr: float,
        risk_tolerance: float,
        window_start_block: int,
        window_end_block: int,
        price_forecasts: List[Dict[str, Any]],  # 96 blocks: {block_id, predicted_price, lower_bound, upper_bound}
        load_forecasts: List[Dict[str, Any]],   # 96 blocks: {block_id, consumption_kw}
        landing_surcharge_inr: float = 2.45
    ) -> Dict[str, Any]:
        
        prob = pulp.LpProblem(f"GreenWatt_Optimization_{facility_id}", pulp.LpMinimize)
        
        blocks = range(window_start_block, window_end_block + 1)
        
        # Lookups
        load_map = {item["block_id"]: float(item["consumption_kw"]) for item in load_forecasts}
        price_map = {item["block_id"]: item for item in price_forecasts}
        
        # Decision Variables
        p_dam = pulp.LpVariable.dicts("P_DAM", blocks, lowBound=0, cat=pulp.LpContinuous)
        p_rtm = pulp.LpVariable.dicts("P_RTM", blocks, lowBound=0, cat=pulp.LpContinuous)
        p_discom = pulp.LpVariable.dicts("P_DISCOM", blocks, lowBound=0, cat=pulp.LpContinuous)
        
        cost_expressions = []
        discom_fallback_blocks = []

        # Risk-tolerance limits: Higher risk_tolerance gives RTM more room (up to 75% of demand)
        max_rtm_fraction = min(0.85, max(0.05, risk_tolerance * 0.85))

        for b in blocks:
            required_kw = load_map.get(b, 500.0)
            p_data = price_map.get(b, {"predicted_price": 5.0, "lower_bound": 4.2, "upper_bound": 6.1})
            
            # Effective exchange landing price = Market Price + State Surcharges
            dam_landing_est = (p_data["predicted_price"] / 1000.0) + landing_surcharge_inr  # p_data in INR/MWh or INR/kWh
            # RTM uses conservative upper bound if risk tolerance is low
            effective_rtm_price = (p_data["lower_bound"] if risk_tolerance > 0.6 else p_data["upper_bound"]) + landing_surcharge_inr

            # Price-Spike Guard: If exchange is expected to exceed ceiling or DISCOM tariff, trigger fallback
            if dam_landing_est > ceiling_price_inr and effective_rtm_price > ceiling_price_inr:
                prob += p_discom[b] == required_kw
                prob += p_dam[b] == 0
                prob += p_rtm[b] == 0
                discom_fallback_blocks.append(b)
            else:
                # Supply-Demand Balance
                prob += (p_dam[b] + p_rtm[b] + p_discom[b] == required_kw)
                
                # Risk Constraint on RTM
                prob += (p_rtm[b] <= max_rtm_fraction * required_kw)
                
                # Penalize DISCOM purchase when prices are safely under ceiling
                cost_expressions.append(dam_landing_est * p_dam[b])
                cost_expressions.append(effective_rtm_price * p_rtm[b])
                cost_expressions.append(discom_tariff_inr * p_discom[b] * 1.5)  # Penalty weight

        prob += pulp.lpSum(cost_expressions)
        prob.solve(pulp.PULP_CBC_CMD(msg=False))

        # Compile Schedule
        block_allocations = []
        total_dam_kwh = 0.0
        total_rtm_kwh = 0.0
        total_discom_kwh = 0.0

        for b in blocks:
            dam_val = round(pulp.value(p_dam[b]) or 0.0, 2)
            rtm_val = round(pulp.value(p_rtm[b]) or 0.0, 2)
            discom_val = round(pulp.value(p_discom[b]) or 0.0, 2)

            total_dam_kwh += dam_val * 0.25  # 15-min interval = 0.25h
            total_rtm_kwh += rtm_val * 0.25
            total_discom_kwh += discom_val * 0.25

            block_allocations.append({
                "block_id": b,
                "dam_allocation_kw": dam_val,
                "rtm_allocation_kw": rtm_val,
                "discom_allocation_kw": discom_val,
                "is_fallback": b in discom_fallback_blocks
            })

        total_req_kwh = total_dam_kwh + total_rtm_kwh + total_discom_kwh

        return {
            "status": pulp.LpStatus[prob.status],
            "plan_date": plan_date,
            "facility_id": facility_id,
            "dam_total_mw": round(total_dam_kwh / 250.0, 3),
            "rtm_total_mw": round(total_rtm_kwh / 250.0, 3),
            "discom_fallback_blocks": discom_fallback_blocks,
            "total_dam_kwh": round(total_dam_kwh, 2),
            "total_rtm_kwh": round(total_rtm_kwh, 2),
            "total_discom_kwh": round(total_discom_kwh, 2),
            "dam_share_pct": round((total_dam_kwh / total_req_kwh) * 100, 1) if total_req_kwh > 0 else 0,
            "rtm_share_pct": round((total_rtm_kwh / total_req_kwh) * 100, 1) if total_req_kwh > 0 else 0,
            "discom_share_pct": round((total_discom_kwh / total_req_kwh) * 100, 1) if total_req_kwh > 0 else 0,
            "block_allocations": block_allocations
        }
