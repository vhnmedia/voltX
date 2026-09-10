'use client';
import React, { useState } from 'react';
import Navbar from '../../components/layout/Navbar';

export default function PlannerPage() {
  const [riskTolerance, setRiskTolerance] = useState(0.4);
  const [ceilingPrice, setCeilingPrice] = useState(6.20);
  const [windowStart, setWindowStart] = useState(1);
  const [windowEnd, setWindowEnd] = useState(96);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [planResult, setPlanResult] = useState<any>(null);

  const handleRunOptimizer = () => {
    setIsOptimizing(true);
    // Simulates calling /api/planner/optimize
    setTimeout(() => {
      const damShare = Math.round((1 - riskTolerance * 0.6) * 100);
      const rtmShare = 100 - damShare - 3;
      setPlanResult({
        plan_id: 'plan-d83a1b',
        dam_total_mw: 0.85,
        rtm_total_mw: 0.35,
        dam_share_pct: damShare,
        rtm_share_pct: rtmShare,
        discom_share_pct: 3,
        discom_fallback_blocks: [78, 79], // Blocks exceeding ceiling
        estimated_cost_inr: 102450,
        discom_baseline_cost_inr: 147000,
        expected_savings_inr: 44550
      });
      setIsOptimizing(false);
    }, 600);
  };

  return (
    <div className="min-h-screen bg-white text-black">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="border-b border-neutral-200 pb-4 mb-6">
          <h1 className="text-xl font-black text-black">LP Power Procurement Optimizer</h1>
          <p className="text-xs text-neutral-500 mt-1">
            Solves optimal DAM vs. RTM MW allocation under price uncertainty and price-spike safety guards.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Controls Form */}
          <div className="p-6 border border-neutral-200 rounded-lg bg-white space-y-6 shadow-sm">
            <h2 className="text-sm font-bold uppercase tracking-wider text-black">Parameters</h2>

            <div>
              <div className="flex justify-between text-xs font-semibold mb-2">
                <span>Risk Tolerance (RTM Exposure)</span>
                <span className="text-blue-600 font-bold">{riskTolerance}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={riskTolerance}
                onChange={(e) => setRiskTolerance(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-neutral-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-[10px] text-neutral-400 mt-1">
                <span>0.0 (100% DAM baseline)</span>
                <span>1.0 (Max RTM dip targeting)</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-neutral-700 mb-1">
                Max Ceiling Price (INR / kWh)
              </label>
              <input
                type="number"
                step="0.1"
                value={ceilingPrice}
                onChange={(e) => setCeilingPrice(parseFloat(e.target.value))}
                className="w-full px-3 py-2 text-sm border border-neutral-300 rounded focus:outline-none focus:border-blue-600"
              />
              <p className="text-[11px] text-neutral-400 mt-1">
                Blocks exceeding ceiling will route to DISCOM Fallback.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-neutral-700 mb-1">Start Block (1-96)</label>
                <input
                  type="number"
                  value={windowStart}
                  onChange={(e) => setWindowStart(parseInt(e.target.value))}
                  className="w-full px-3 py-2 text-sm border border-neutral-300 rounded focus:outline-none focus:border-blue-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-neutral-700 mb-1">End Block (1-96)</label>
                <input
                  type="number"
                  value={windowEnd}
                  onChange={(e) => setWindowEnd(parseInt(e.target.value))}
                  className="w-full px-3 py-2 text-sm border border-neutral-300 rounded focus:outline-none focus:border-blue-600"
                />
              </div>
            </div>

            <button
              onClick={handleRunOptimizer}
              disabled={isOptimizing}
              className="w-full py-2.5 px-4 bg-black text-white text-xs font-bold uppercase tracking-wider rounded hover:bg-neutral-800 transition"
            >
              {isOptimizing ? 'Solving Linear Program...' : 'Solve LP Allocation'}
            </button>
          </div>

          {/* Solution & Decision View */}
          <div className="lg:col-span-2 space-y-6">
            {planResult ? (
              <div className="border border-neutral-200 rounded-lg p-6 bg-white shadow-sm space-y-6">
                <div className="flex items-center justify-between border-b border-neutral-100 pb-4">
                  <div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                      Optimal Plan Generated
                    </span>
                    <h3 className="text-lg font-bold text-black mt-1">Allocation Strategy for Next Day</h3>
                  </div>
                  <button className="px-5 py-2.5 bg-blue-600 text-white text-xs font-bold uppercase tracking-wider rounded hover:bg-blue-700 transition">
                    Approve & Route Bids
                  </button>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 bg-neutral-50 rounded border border-neutral-100">
                    <p className="text-xs text-neutral-500 font-medium">DAM Allocation (Locked)</p>
                    <p className="text-xl font-bold text-black mt-1">{planResult.dam_share_pct}%</p>
                    <p className="text-[11px] text-neutral-400 mt-0.5">{planResult.dam_total_mw} MW avg</p>
                  </div>
                  <div className="p-4 bg-neutral-50 rounded border border-neutral-100">
                    <p className="text-xs text-neutral-500 font-medium">RTM Allocation (Flexible)</p>
                    <p className="text-xl font-bold text-blue-600 mt-1">{planResult.rtm_share_pct}%</p>
                    <p className="text-[11px] text-neutral-400 mt-0.5">{planResult.rtm_total_mw} MW avg</p>
                  </div>
                  <div className="p-4 bg-neutral-50 rounded border border-neutral-100">
                    <p className="text-xs text-neutral-500 font-medium">DISCOM Fallback</p>
                    <p className="text-xl font-bold text-neutral-800 mt-1">{planResult.discom_share_pct}%</p>
                    <p className="text-[11px] text-neutral-400 mt-0.5">Blocks: {planResult.discom_fallback_blocks.join(', ')}</p>
                  </div>
                </div>

                <div className="p-4 border border-blue-200 bg-blue-50/50 rounded flex justify-between items-center">
                  <div>
                    <p className="text-xs font-semibold text-black">Estimated Net Daily Savings</p>
                    <p className="text-xs text-neutral-500">Against standard DISCOM flat-tariff baseline</p>
                  </div>
                  <p className="text-2xl font-black text-blue-700">₹{planResult.expected_savings_inr.toLocaleString()}</p>
                </div>
              </div>
            ) : (
              <div className="border border-dashed border-neutral-300 rounded-lg p-12 text-center text-neutral-400">
                <p className="text-sm">Configure parameters and click "Solve LP Allocation" to generate an optimized procurement schedule.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
