'use client';
import React, { useState } from 'react';
import Navbar from '../../components/layout/Navbar';

export default function KYCPage() {
  const [gstin, setGstin] = useState('24AABCU9603R1ZM');
  const [orgName, setOrgName] = useState('VHN Media Campus');
  const [stateCode, setStateCode] = useState('GJ');
  const [demandKw, setDemandKw] = useState(1200);
  const [isGreenOA, setIsGreenOA] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleVerify = () => {
    // Calls compliance stub
    const minThreshold = isGreenOA ? 100 : 1000;
    const isEligible = demandKw >= minThreshold;
    setResult({
      gstin_valid: true,
      verified_name: orgName,
      eligible: isEligible,
      state: stateCode,
      surcharges: {
        css: 1.65,
        add: 0.40,
        wheeling: 0.19,
        transmission: 0.38,
        total: 2.62
      }
    });
  };

  return (
    <div className="min-h-screen bg-white text-black">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="text-xl font-black text-black">KYC & Open Access Eligibility Check</h1>
        <p className="text-xs text-neutral-500 mt-1 mb-6">
          Verifies enterprise identity and computes cross-subsidy and wheeling surcharges under state SERC orders.
        </p>

        <div className="p-6 border border-neutral-200 rounded-lg bg-white space-y-4 shadow-sm">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-neutral-700 mb-1">GSTIN Number</label>
              <input
                type="text"
                value={gstin}
                onChange={(e) => setGstin(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-neutral-300 rounded font-mono focus:border-blue-600 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-neutral-700 mb-1">Organization Legal Name</label>
              <input
                type="text"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-neutral-300 rounded focus:border-blue-600 outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-neutral-700 mb-1">State Jurisdiction</label>
              <select
                value={stateCode}
                onChange={(e) => setStateCode(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-neutral-300 rounded focus:border-blue-600 outline-none"
              >
                <option value="GJ">Gujarat (Torrent / GUVNL)</option>
                <option value="MH">Maharashtra (MSEDCL / TPC)</option>
                <option value="TN">Tamil Nadu (TANGEDCO)</option>
                <option value="KA">Karnataka (BESCOM)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-neutral-700 mb-1">Contracted Demand (kW)</label>
              <input
                type="number"
                value={demandKw}
                onChange={(e) => setDemandKw(parseFloat(e.target.value))}
                className="w-full px-3 py-2 text-sm border border-neutral-300 rounded focus:border-blue-600 outline-none"
              />
            </div>
            <div className="flex items-center pt-6">
              <label className="flex items-center text-xs font-medium cursor-pointer">
                <input
                  type="checkbox"
                  checked={isGreenOA}
                  onChange={(e) => setIsGreenOA(e.target.checked)}
                  className="rounded text-blue-600 mr-2"
                />
                Green Energy OA (100 kW min)
              </label>
            </div>
          </div>

          <button
            onClick={handleVerify}
            className="w-full py-2.5 bg-blue-600 text-white text-xs font-bold uppercase tracking-wider rounded hover:bg-blue-700 transition"
          >
            Validate Eligibility & Calculate Surcharges
          </button>
        </div>

        {result && (
          <div className="mt-6 p-6 border border-neutral-200 rounded-lg bg-neutral-50 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className={`text-xs px-2.5 py-0.5 rounded font-bold ${result.eligible ? 'bg-black text-white' : 'bg-neutral-300 text-neutral-700'}`}>
                  {result.eligible ? 'ELIGIBLE FOR OPEN ACCESS' : 'INELIGIBLE: DEMAND BELOW THRESHOLD'}
                </span>
                <p className="text-xs text-neutral-500 mt-1">Mock KYC Format: Verified active status on stub.</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-neutral-500">Landing Surcharge Adder</p>
                <p className="text-xl font-bold text-black">₹{result.surcharges.total} / kWh</p>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-2 pt-2 border-t border-neutral-200 text-xs">
              <div>
                <span className="text-neutral-400">Cross-Subsidy:</span>
                <p className="font-semibold">₹{result.surcharges.css}/kWh</p>
              </div>
              <div>
                <span className="text-neutral-400">Addl. Surcharge:</span>
                <p className="font-semibold">₹{result.surcharges.add}/kWh</p>
              </div>
              <div>
                <span className="text-neutral-400">Wheeling Charges:</span>
                <p className="font-semibold">₹{result.surcharges.wheeling}/kWh</p>
              </div>
              <div>
                <span className="text-neutral-400">Transmission:</span>
                <p className="font-semibold">₹{result.surcharges.transmission}/kWh</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
