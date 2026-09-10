'use client';
import React from 'react';
import Navbar from '../../components/layout/Navbar';

export default function ReportsPage() {
  return (
    <div className="min-h-screen bg-white text-black">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex justify-between items-center border-b border-neutral-200 pb-4 mb-6">
          <div>
            <h1 className="text-xl font-black text-black">Reconciliation & CO₂ Impact</h1>
            <p className="text-xs text-neutral-500 mt-1">Monthly performance against baseline DISCOM tariffs</p>
          </div>
          <button className="px-4 py-2 bg-blue-600 text-white text-xs font-bold uppercase tracking-wider rounded hover:bg-blue-700 transition">
            Export PDF
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="p-6 border border-neutral-200 rounded-lg bg-white shadow-sm space-y-6">
            <div>
              <h2 className="text-sm font-bold text-black uppercase tracking-wider">Financial Savings</h2>
              <p className="text-[11px] text-neutral-500">Current Month (Estimated)</p>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center pb-3 border-b border-neutral-100">
                <span className="text-sm text-neutral-600">Total Consumption</span>
                <span className="text-sm font-bold">142.5 MWh</span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b border-neutral-100">
                <span className="text-sm text-neutral-600">Baseline DISCOM Cost</span>
                <span className="text-sm font-bold text-neutral-400 line-through">₹9,97,500</span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b border-neutral-100">
                <span className="text-sm text-neutral-600">Actual Exchange Cost (inc. OA)</span>
                <span className="text-sm font-bold text-black">₹6,84,120</span>
              </div>
              <div className="flex justify-between items-center pt-2">
                <span className="text-sm font-bold text-black">Net Savings</span>
                <span className="text-lg font-black text-blue-600">₹3,13,380 (31.4%)</span>
              </div>
            </div>
          </div>

          <div className="p-6 border border-neutral-200 rounded-lg bg-white shadow-sm space-y-6">
            <div>
              <h2 className="text-sm font-bold text-black uppercase tracking-wider">Carbon Mitigation</h2>
              <p className="text-[11px] text-neutral-500">Proxy estimate via daytime solar displacement</p>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center pb-3 border-b border-neutral-100">
                <span className="text-sm text-neutral-600">Grid Baseline Intensity</span>
                <span className="text-sm font-bold">0.72 kg / kWh</span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b border-neutral-100">
                <span className="text-sm text-neutral-600">Exchange Mix Intensity</span>
                <span className="text-sm font-bold">0.58 kg / kWh</span>
              </div>
              <div className="flex justify-between items-center pt-2">
                <span className="text-sm font-bold text-black">Estimated CO₂ Avoided</span>
                <span className="text-lg font-black text-black">19.95 Tons</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
