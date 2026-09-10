'use client';
import React, { useState, useEffect } from 'react';
import Navbar from '../../components/layout/Navbar';

export default function LiveMarketPage() {
  const [timeLeft, setTimeLeft] = useState(14 * 60 + 23); // 14m 23s mock countdown

  useEffect(() => {
    const timer = setInterval(() => setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0)), 1000);
    return () => clearInterval(timer);
  }, []);

  const mins = Math.floor(timeLeft / 60);
  const secs = timeLeft % 60;

  return (
    <div className="min-h-screen bg-white text-black">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex justify-between items-end border-b border-neutral-200 pb-4 mb-6">
          <div>
            <h1 className="text-xl font-black text-black">Live RTM Market View</h1>
            <p className="text-xs text-neutral-500 mt-1">Real-Time Market (RTM) nearest gate closure</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider mb-1">Next Gate Closure (Block 42)</p>
            <p className={`text-2xl font-black font-mono ${timeLeft < 300 ? 'text-red-600' : 'text-blue-600'}`}>
              {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 border border-neutral-200 rounded-lg bg-white shadow-sm flex flex-col justify-center items-center h-48">
            <p className="text-xs font-semibold text-neutral-500 uppercase tracking-widest mb-2">Current RTM Clearing</p>
            <p className="text-5xl font-black text-black">₹4.15</p>
            <p className="text-xs text-blue-600 font-medium mt-3">Block 41 Executing</p>
          </div>

          <div className="col-span-2 p-6 border border-neutral-200 rounded-lg bg-black text-white shadow-sm flex flex-col justify-center h-48">
            <div className="flex justify-between items-center w-full">
              <div>
                <p className="text-xs font-semibold text-neutral-400 uppercase tracking-widest mb-1">Pending Automated Bid</p>
                <p className="text-3xl font-black text-white">450 <span className="text-lg font-medium text-neutral-400">kW</span></p>
                <p className="text-sm text-neutral-300 mt-1">Ceiling: ₹5.50 / kWh</p>
              </div>
              <div className="text-right">
                <span className="px-3 py-1 bg-blue-600 text-white text-[10px] font-bold rounded shadow shadow-blue-900/50">QUEUED</span>
                <p className="text-[10px] text-neutral-500 mt-3 font-mono">ID: RTM-B42-99A</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
