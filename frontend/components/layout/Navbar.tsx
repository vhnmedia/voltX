import React from 'react';
import Link from 'next/link';

export default function Navbar() {
  return (
    <header className="border-b border-neutral-200 bg-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-black flex items-center justify-center text-white font-bold text-lg tracking-tighter">
            GW
          </div>
          <div>
            <span className="font-extrabold text-black tracking-tight text-lg">GreenWatt</span>
            <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
              IEX Layer
            </span>
          </div>
        </div>
        <nav className="flex space-x-1">
          <Link href="/" className="px-3 py-2 text-sm font-medium text-neutral-600 hover:text-black hover:bg-neutral-50 rounded-md">
            Overview
          </Link>
          <Link href="/planner" className="px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md">
            LP Planner
          </Link>
          <Link href="/live" className="px-3 py-2 text-sm font-medium text-neutral-600 hover:text-black hover:bg-neutral-50 rounded-md">
            Live Market
          </Link>
          <Link href="/trades" className="px-3 py-2 text-sm font-medium text-neutral-600 hover:text-black hover:bg-neutral-50 rounded-md">
            Trade Ledger
          </Link>
          <Link href="/kyc" className="px-3 py-2 text-sm font-medium text-neutral-600 hover:text-black hover:bg-neutral-50 rounded-md">
            KYC & OA Rules
          </Link>
          <Link href="/reports" className="px-3 py-2 text-sm font-medium text-neutral-600 hover:text-black hover:bg-neutral-50 rounded-md">
            Savings & CO₂
          </Link>
        </nav>
        <div className="flex items-center space-x-2">
          <div className="text-right text-xs">
            <p className="font-semibold text-black">Adani Campus Node</p>
            <p className="text-neutral-400">DISCOM: Torrent Power (GJ)</p>
          </div>
        </div>
      </div>
    </header>
  );
}
