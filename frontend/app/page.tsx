'use client';
import React, { useState } from 'react';
import Navbar from '../components/layout/Navbar';
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend
} from 'recharts';

// Seeded 96-block simulation data
const mockForecastData = Array.from({ length: 96 }, (_, i) => {
  const block = i + 1;
  const isSolar = block >= 36 && block <= 68;
  const basePrice = isSolar ? 3.8 + Math.sin(block / 5) * 0.4 : 5.4 + Math.cos(block / 4) * 0.8;
  return {
    block,
    time: `${String(Math.floor(i / 4)).padStart(2, '0')}:${String((i % 4) * 15).padStart(2, '0')}`,
    predicted_price: Number(basePrice.toFixed(2)),
    lower_bound: Number((basePrice * 0.85).toFixed(2)),
    upper_bound: Number((basePrice * 1.22).toFixed(2)),
    load_kw: isSolar ? 1150 + Math.floor(Math.random() * 80) : 480 + Math.floor(Math.random() * 40),
  };
});

export default function HomeDashboard() {
  const [data] = useState(mockForecastData);

  return (
    <div className="min-h-screen bg-white text-black">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        
        {/* KPI Strip */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-5 border border-neutral-200 rounded-lg bg-white shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500">Day's Weighted DAM MCP</p>
            <p className="text-2xl font-black text-black mt-1">₹4.62 <span className="text-sm font-normal text-neutral-500">/ kWh</span></p>
            <p className="text-xs text-blue-600 font-medium mt-2">↓ 34.0% vs Fixed DISCOM (₹7.00)</p>
          </div>
          <div className="p-5 border border-neutral-200 rounded-lg bg-white shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500">Projected Day Load</p>
            <p className="text-2xl font-black text-black mt-1">18.42 <span className="text-sm font-normal text-neutral-500">MWh</span></p>
            <p className="text-xs text-neutral-500 mt-2">Peak: 1.25 MW (Block 48)</p>
          </div>
          <div className="p-5 border border-neutral-200 rounded-lg bg-white shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500">Estimated Daily Savings</p>
            <p className="text-2xl font-black text-blue-600 mt-1">₹43,810</p>
            <p className="text-xs text-neutral-500 mt-2">LP Allocation: 68% DAM / 32% RTM</p>
          </div>
          <div className="p-5 border border-neutral-200 rounded-lg bg-white shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500">Renewable Displacement</p>
            <p className="text-2xl font-black text-black mt-1">3,420 <span className="text-sm font-normal text-neutral-500">kg CO₂</span></p>
            <p className="text-xs text-neutral-400 mt-2">Proxy estimate (solar block match)</p>
          </div>
        </div>

        {/* Price Forecast Chart with Uncertainty Band */}
        <div className="border border-neutral-200 rounded-lg p-6 bg-white shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-black">96-Block MCP Price Forecast & Confidence Band</h2>
              <p className="text-xs text-neutral-500">XGBoost Quantile Regressor (10th to 90th percentile interval) in INR/kWh</p>
            </div>
            <div className="flex items-center space-x-3 text-xs">
              <span className="flex items-center"><span className="w-3 h-3 bg-blue-600 rounded-full mr-1"></span> Predicted MCP</span>
              <span className="flex items-center"><span className="w-3 h-3 bg-blue-100 rounded-sm mr-1"></span> 80% Confidence Band</span>
            </div>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="time" interval={8} tick={{ fill: '#737373', fontSize: 11 }} />
                <YAxis tick={{ fill: '#737373', fontSize: 11 }} domain={[2, 8]} />
                <Tooltip contentStyle={{ backgroundColor: '#000', borderRadius: '4px', border: 'none', color: '#fff', fontSize: '12px' }} />
                <Area type="monotone" dataKey="upper_bound" stroke="transparent" fill="#dbeafe" fillOpacity={0.6} />
                <Area type="monotone" dataKey="lower_bound" stroke="transparent" fill="#ffffff" fillOpacity={1} />
                <Line type="monotone" dataKey="predicted_price" stroke="#2563eb" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Load Forecast Chart */}
        <div className="border border-neutral-200 rounded-lg p-6 bg-white shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-black">Facility Load Prediction (LightGBM)</h2>
              <p className="text-xs text-neutral-500">15-minute interval expected draw (kW) based on weather and campus schedules</p>
            </div>
          </div>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="time" interval={8} tick={{ fill: '#737373', fontSize: 11 }} />
                <YAxis tick={{ fill: '#737373', fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#000', borderRadius: '4px', border: 'none', color: '#fff', fontSize: '12px' }} />
                <Line type="monotone" dataKey="load_kw" stroke="#0f172a" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </main>
    </div>
  );
}
