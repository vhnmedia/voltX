"""
compliance.py - Regulatory & Open-Access Compliance Engine

IMPORTANT FRAMING & SIMULATION NOTICE:
- The KYC verification module is a format-validation stub and does NOT hit the
  live GSTN API or MCA portal. Production systems require a licensed KYC/GSP partner.
- The open-access surcharge schedule is an approximation across 4 benchmark states
  (Maharashtra, Gujarat, Tamil Nadu, Karnataka). Full pan-India tariff orders require
  continuous SERC tariff order tracking.
"""

import re
from typing import Dict, Any
from supabase_client import supabase

# Seed reference data for open-access calculation
STATE_BENCHMARKS = {
    "GJ": {
        "state_name": "Gujarat",
        "min_demand_kw": 1000.0,
        "green_oa_min_demand_kw": 100.0,
        "cross_subsidy_surcharge_inr": 1.65,
        "additional_surcharge_inr": 0.40,
        "wheeling_charges_inr": 0.19,
        "transmission_charges_inr": 0.38
    },
    "MH": {
        "state_name": "Maharashtra",
        "min_demand_kw": 1000.0,
        "green_oa_min_demand_kw": 100.0,
        "cross_subsidy_surcharge_inr": 1.98,
        "additional_surcharge_inr": 1.25,
        "wheeling_charges_inr": 0.85,
        "transmission_charges_inr": 0.42
    },
    "TN": {
        "state_name": "Tamil Nadu",
        "min_demand_kw": 1000.0,
        "green_oa_min_demand_kw": 100.0,
        "cross_subsidy_surcharge_inr": 1.80,
        "additional_surcharge_inr": 0.00,
        "wheeling_charges_inr": 0.22,
        "transmission_charges_inr": 0.45
    },
    "KA": {
        "state_name": "Karnataka",
        "min_demand_kw": 1000.0,
        "green_oa_min_demand_kw": 100.0,
        "cross_subsidy_surcharge_inr": 1.75,
        "additional_surcharge_inr": 0.60,
        "wheeling_charges_inr": 0.35,
        "transmission_charges_inr": 0.40
    }
}

GSTIN_REGEX = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"

class ComplianceEngine:
    @staticmethod
    def verify_gstin_stub(gstin: str, org_name: str) -> Dict[str, Any]:
        """Validates GSTIN structure and generates mock verification."""
        clean_gstin = gstin.strip().upper()
        if not re.match(GSTIN_REGEX, clean_gstin):
            return {
                "valid": False,
                "verified": False,
                "error": "Invalid GSTIN format. Expected format: 22AAAAA0000A1Z5",
                "is_simulated": True
            }
        
        state_code_num = clean_gstin[:2]
        pan = clean_gstin[2:12]
        
        return {
            "valid": True,
            "verified": True,
            "gstin": clean_gstin,
            "extracted_pan": pan,
            "state_code_numeric": state_code_num,
            "legal_entity_name": org_name,
            "status": "ACTIVE",
            "is_simulated": True,
            "note": "SIMULATION ONLY: Verified format against mock GSTN registry."
        }

    @classmethod
    def evaluate_open_access_eligibility(cls, state_code: str, contracted_demand_kw: float, is_green_oa: bool = False) -> Dict[str, Any]:
        """Calculates open-access eligibility and landing surcharges."""
        state = state_code.upper()
        if state not in STATE_BENCHMARKS:
            return {
                "eligible": False,
                "reason": f"State {state} is outside the active 4-state pilot (GJ, MH, TN, KA).",
                "benchmarks": None
            }

        rule = STATE_BENCHMARKS[state]
        threshold = rule["green_oa_min_demand_kw"] if is_green_oa else rule["min_demand_kw"]
        is_eligible = contracted_demand_kw >= threshold

        total_oa_surcharges_inr = (
            rule["cross_subsidy_surcharge_inr"] +
            rule["additional_surcharge_inr"] +
            rule["wheeling_charges_inr"] +
            rule["transmission_charges_inr"]
        )

        return {
            "eligible": is_eligible,
            "state_code": state,
            "contracted_demand_kw": contracted_demand_kw,
            "required_threshold_kw": threshold,
            "rule_basis": "Green Energy OA (2022 Rules)" if is_green_oa else "Standard Open Access (>1MW)",
            "surcharge_breakdown_inr_kwh": {
                "cross_subsidy_surcharge": rule["cross_subsidy_surcharge_inr"],
                "additional_surcharge": rule["additional_surcharge_inr"],
                "wheeling_charges": rule["wheeling_charges_inr"],
                "transmission_charges": rule["transmission_charges_inr"],
                "total_landing_surcharge": round(total_oa_surcharges_inr, 3)
            }
        }
