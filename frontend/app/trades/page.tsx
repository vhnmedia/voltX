'use client';
import React, { useState } from 'react';
import Navbar from '../../components/layout/Navbar';

const mockTrades = [
  { id: 'TL-101', block: 38, time: '09:15', market: 'DAM', qty: 650, bid: 4.80, cleared: 4.62, status: 'cleared', ref: 'SIM-CLR-92FA' },
  { id: 'TL-102', block: 39, time: '09:30', market: 'RTM', qty: 220, bid: 4.20, cleared: 4.05, status: 'cleared', ref: 'SIM-CLR-8B31' },
  { id: 'TL-103', block: 78, time: '19:30', market: 'DISCOM', qty: 850, bid: 6.20, cleared: null, status: 'discom_fallback', ref: 'DISCOM-SAFETY-VALVE' },
  { id: 'TL-104', block: 79, time: '19:45', market: 'RTM', qty: 300, bid: 6.20, cleared: null, status: 'missed', ref: 'SIM-REJ-42B1' },
];

export default function TradeHistoryPage() {
  const [trades] = useState(mockTrades);

  return (
    <div className="min-h-screen bg-white text-black">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-xl font-black text-black">Trade Execution Ledger</h1>
            <p className="text-xs text-neutral-500">Live feed of orders routed via simulated trading-partner API</p>
          </div>
          <span className="text-xs px-2.5 py-1 bg-neutral-100 text-neutral-700 font-mono rounded">
            SIMULATED EXECUTION
          </span>
        </div>

        <div className="border border-neutral-200 rounded-lg overflow-hidden shadow-sm">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-neutral-50 border-b border-neutral-200 text-neutral-500 font-semibold uppercase">
                <th className="p-3">Order ID</th>
                <th className="p-3">Block / Time</th>
                <th className="p-3">Market</th>
                <th className="p-3">Quantity (kW)</th>
                <th className="p-3">Bid Price</th>
                <th className="p-3">Cleared Price</th>
                <th className="p-3">Status</th>
                <th className="p-3">Partner Reference</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {trades.map((t) => (
                <tr key={t.id} className="hover:bg-neutral-50/60 transition">
                  <td className="p-3 font-mono font-bold text-black">{t.id}</td>
                  <td className="p-3 text-neutral-700">Block {t.block} ({t.time})</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded font-medium ${
                      t.market === 'DAM' ? 'bg-neutral-100 text-neutral-800' :
                      t.market === 'RTM' ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-800'
                    }`}>
                      {t.market}
                    </span>
                  </td>
                  <td className="p-3 font-medium text-black">{t.qty} kW</td>
                  <td className="p-3 text-neutral-600">₹{t.bid.toFixed(2)}</td>
                  <td className="p-3 text-neutral-900 font-bold">{t.cleared ? `₹${t.cleared.toFixed(2)}` : '—'}</td>
                  <td className="p-3">
                    {t.status === 'cleared' && (
                      <span className="px-2 py-0.5 rounded bg-blue-600 text-white font-semibold text-[10px]">CLEARED</span>
                    )}
                    {t.status === 'discom_fallback' && (
                      <span className="px-2 py-0.5 rounded bg-neutral-800 text-white font-semibold text-[10px]">DISCOM FALLBACK</span>
                    )}
                    {t.status === 'missed' && (
                      <span className="px-2 py-0.5 rounded bg-neutral-200 text-neutral-700 font-semibold text-[10px]">MISSED (SPIKE)</span>
                    )}
                  </td>
                  <td className="p-3 font-mono text-neutral-400 text-[11px]">{t.ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
