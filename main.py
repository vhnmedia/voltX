"""
main.py - GreenWatt Central API Engine
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

from supabase_client import supabase
from compliance import ComplianceEngine
from optimizer import PowerProcurementOptimizer
from execution import ExecutionOrchestrator
from reconciliation import ReconciliationService
# Imports user's existing ML forecasting logic
try:
    from forecasting import generate_price_forecast, generate_load_forecast
except ImportError:
    # Fallback stubs if running isolated test
    def generate_price_forecast(target_date: str):
        return [{"block_id": b, "predicted_price": 4.5 + (0.5 if 36 <= b <= 68 else 1.2), "lower_bound": 3.8, "upper_bound": 5.9} for b in range(1, 97)]
    def generate_load_forecast(facility_id: str, target_date: str):
        return [{"block_id": b, "consumption_kw": 850.0 if 36 <= b <= 72 else 420.0} for b in range(1, 97)]

app = FastAPI(
    title="GreenWatt Intelligent Energy Procurement Engine",
    description="Decision-support & automated bidding platform for Indian Commercial C&I consumers.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class KYCVerificationRequest(BaseModel):
    gstin: str
    org_name: str

class OpenAccessCheckRequest(BaseModel):
    state_code: str
    contracted_demand_kw: float
    is_green_oa: bool = False

class PlanOptimizationRequest(BaseModel):
    facility_id: str
    plan_date: str
    ceiling_price_inr: float = Field(..., gt=0)
    risk_tolerance: float = Field(0.5, ge=0.0, le=1.0)
    window_start_block: int = Field(1, ge=1, le=96)
    window_end_block: int = Field(96, ge=1, le=96)

class PlanApprovalRequest(BaseModel):
    plan_id: str
    user_id: str

# --- Endpoints ---

@app.get("/")
def health_check():
    return {"status": "online", "platform": "GreenWatt API", "version": "1.0.0"}

@app.post("/api/compliance/verify-gstin")
def verify_gstin(req: KYCVerificationRequest):
    return ComplianceEngine.verify_gstin_stub(req.gstin, req.org_name)

@app.post("/api/compliance/check-open-access")
def check_open_access(req: OpenAccessCheckRequest):
    return ComplianceEngine.evaluate_open_access_eligibility(
        req.state_code, req.contracted_demand_kw, req.is_green_oa
    )

@app.get("/api/market/forecasts")
def get_forecasts(target_date: str, facility_id: str):
    prices = generate_price_forecast(target_date)
    loads = generate_load_forecast(facility_id, target_date)
    return {
        "target_date": target_date,
        "facility_id": facility_id,
        "price_forecast": prices,
        "load_forecast": loads
    }

@app.post("/api/planner/optimize")
def optimize_procurement(req: PlanOptimizationRequest):
    fac = supabase.table("facilities").select("*").eq("id", req.facility_id).single().execute().data
    if not fac:
        raise HTTPException(status_code=404, detail="Facility not found")

    price_forecasts = generate_price_forecast(req.plan_date)
    load_forecasts = generate_load_forecast(req.facility_id, req.plan_date)

    optimization_res = PowerProcurementOptimizer.run_optimization(
        plan_date=req.plan_date,
        facility_id=req.facility_id,
        discom_tariff_inr=float(fac["discom_tariff_inr_per_kwh"]),
        ceiling_price_inr=req.ceiling_price_inr,
        risk_tolerance=req.risk_tolerance,
        window_start_block=req.window_start_block,
        window_end_block=req.window_end_block,
        price_forecasts=price_forecasts,
        load_forecasts=load_forecasts
    )

    # Persist draft plan
    plan_record = {
        "facility_id": req.facility_id,
        "plan_date": req.plan_date,
        "status": "pending_approval",
        "required_load_kw": fac["contracted_demand_kw"],
        "ceiling_price_inr_per_kwh": req.ceiling_price_inr,
        "risk_tolerance": req.risk_tolerance,
        "window_start_block": req.window_start_block,
        "window_end_block": req.window_end_block,
        "dam_allocation_mw": optimization_res["dam_total_mw"],
        "rtm_allocation_mw": optimization_res["rtm_total_mw"],
        "discom_fallback_blocks": optimization_res["discom_fallback_blocks"],
        "optimizer_notes": f"Generated with risk factor {req.risk_tolerance}."
    }
    inserted = supabase.table("procurement_plans").insert(plan_record).execute()
    plan_id = inserted.data[0]["id"]

    return {"plan_id": plan_id, **optimization_res}

@app.post("/api/planner/approve")
def approve_and_execute_plan(req: PlanApprovalRequest):
    plan = supabase.table("procurement_plans").select("*").eq("id", req.plan_id).single().execute().data
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Update status to approved
    supabase.table("procurement_plans").update({
        "status": "executing",
        "approved_by": req.user_id,
        "approved_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }).eq("id", req.plan_id).execute()

    # Re-run or fetch allocations and execute orders
    price_forecasts = generate_price_forecast(plan["plan_date"])
    load_forecasts = generate_load_forecast(plan["facility_id"], plan["plan_date"])
    fac = supabase.table("facilities").select("*").eq("id", plan["facility_id"]).single().execute().data

    opt = PowerProcurementOptimizer.run_optimization(
        plan_date=plan["plan_date"],
        facility_id=plan["facility_id"],
        discom_tariff_inr=float(fac["discom_tariff_inr_per_kwh"]),
        ceiling_price_inr=float(plan["ceiling_price_inr_per_kwh"]),
        risk_tolerance=float(plan["risk_tolerance"]),
        window_start_block=plan["window_start_block"],
        window_end_block=plan["window_end_block"],
        price_forecasts=price_forecasts,
        load_forecasts=load_forecasts
    )

    trade_logs = ExecutionOrchestrator.execute_plan_bids(
        plan_id=req.plan_id,
        facility_id=plan["facility_id"],
        plan_date=plan["plan_date"],
        block_allocations=opt["block_allocations"],
        ceiling_price=float(plan["ceiling_price_inr_per_kwh"])
    )

    supabase.table("procurement_plans").update({"status": "completed"}).eq("id", req.plan_id).execute()

    return {
        "status": "completed",
        "executed_trades_count": len(trade_logs),
        "discom_fallback_count": len(opt["discom_fallback_blocks"])
    }

@app.get("/api/reports/reconciliation")
def get_reconciliation(facility_id: str, report_month: str):
    return ReconciliationService.generate_monthly_reconciliation(facility_id, report_month)

@app.get("/api/trades/history")
def get_trades(facility_id: str):
    return supabase.table("trade_logs").select("*").eq("facility_id", facility_id).order("trade_date", desc=True).limit(96).execute().data
