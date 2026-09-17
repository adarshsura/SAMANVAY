import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Sliders, AlertTriangle, ShieldAlert, Zap, Truck, 
  RotateCcw, CheckCircle2, ArrowRight, Play, Ban, RefreshCw 
} from 'lucide-react';

export const SimulationPage: React.FC<{ onNavigateToAdmin?: () => void }> = ({ onNavigateToAdmin }) => {
  const { token } = useAuth();

  const [scenario, setScenario] = useState<string>('Flood Escalation Scenario');
  const [targetZone, setTargetZone] = useState<string>('Zone C');
  const [selectedUnitToDisable, setSelectedUnitToDisable] = useState<string>('AMB-07');
  const [eventLog, setEventLog] = useState<string[]>([
    'Simulation Engine initialized. Baseline fleet: 29 units across 5 zones.'
  ]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const addLog = (msg: string) => {
    setEventLog((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev]);
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const handleStartScenario = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/simulation/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ scenario_name: scenario })
      });
      if (res.ok) {
        addLog(`Started Scenario: ${scenario}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleInjectIncident = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/simulation/event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          event_type: 'INJECT_INCIDENT',
          payload: {
            zone_code: targetZone,
            disaster_type: scenario.includes('Fire') ? 'Fire' : scenario.includes('Collapse') ? 'Building Collapse' : 'Flood',
            reported_people: 180,
            reported_injured: 45,
            reported_trapped: 30
          }
        })
      });
      if (res.ok) {
        const data = await res.json();
        addLog(`Injected Incident ${data.result?.incident_code} in ${targetZone} (45 injured, 30 trapped).`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleBlockRoad = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/simulation/event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          event_type: 'BLOCK_ROAD',
          payload: {
            zone_code: 'Zone B',
            reason: 'Severe flood inundation - 3.5ft water depth'
          }
        })
      });
      if (res.ok) {
        const data = await res.json();
        addLog(`Road blocked in Zone B: ${data.result?.road_name} (Accessibility cut to 15%).`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisableResource = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/simulation/event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          event_type: 'DISABLE_RESOURCE',
          payload: {
            resource_code: selectedUnitToDisable
          }
        })
      });
      if (res.ok) {
        addLog(`Resource ${selectedUnitToDisable} marked UNAVAILABLE (Engine mechanical breakdown).`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSurgeCasualties = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/simulation/event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          event_type: 'SURGE_CASUALTIES',
          payload: {
            incident_code: 'INC-1047',
            added_injured: 40,
            added_trapped: 20,
            added_people: 100
          }
        })
      });
      if (res.ok) {
        const data = await res.json();
        addLog(`Casualties surged in INC-1047: +40 critical victims. Need Score increased to ${data.result?.new_need_score}.`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetSimulation = async () => {
    if (!confirm('Reset simulation state to fresh baseline?')) return;
    setIsLoading(true);
    try {
      const res = await fetch('/api/simulation/reset', {
        method: 'POST',
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) }
      });
      if (res.ok) {
        addLog('Simulation reset. Database restored to baseline seed data.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-slate-100 py-6 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-6">

        {/* Toast Notification */}
        {toastMessage && (
          <div className="fixed top-20 right-6 z-50 p-4 bg-slate-900 text-white rounded-xl shadow-2xl border border-slate-700 flex items-center space-x-2 text-xs">
            <CheckCircle2 className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <span>{toastMessage}</span>
          </div>
        )}

        {/* Header */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="p-2 rounded-lg bg-amber-100 text-amber-700">
                <Sliders className="w-6 h-6" />
              </span>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Disaster Simulation Sandbox</h1>
                <p className="text-xs text-slate-500">
                  Stress-test the OR-Tools MILP optimizer with dynamic casualty surges, road cuts, and vehicle failures.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleResetSimulation}
              disabled={isLoading}
              className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center space-x-1.5 transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset State</span>
            </button>
            {onNavigateToAdmin && (
              <button
                onClick={onNavigateToAdmin}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow flex items-center space-x-1.5 transition"
              >
                <span>View Command Center</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Control Panels Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">

          {/* Left Column: Interactive Scenario Triggers (7 Cols) */}
          <div className="md:col-span-7 space-y-4">
            {/* Step 1: Choose Scenario */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
              <span className="font-bold text-xs text-slate-800 uppercase tracking-wider block">
                1. Select Disaster Scenario
              </span>
              <div className="flex space-x-2">
                <select
                  value={scenario}
                  onChange={(e) => setScenario(e.target.value)}
                  className="flex-1 p-2.5 border border-slate-300 rounded-xl text-xs font-semibold bg-white text-slate-800"
                >
                  <option value="Flood Escalation Scenario">Flood Escalation Scenario (Mutha River Overflow)</option>
                  <option value="Building Collapse Scenario">Building Collapse Scenario (Dense Commercial Collapse)</option>
                  <option value="Fire & Industrial Hazard">Fire & Industrial Hazard (Hadapsar Chemical Belt)</option>
                </select>

                <button
                  onClick={handleStartScenario}
                  disabled={isLoading}
                  className="px-4 py-2.5 bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs rounded-xl shadow flex items-center space-x-1.5"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Start</span>
                </button>
              </div>
            </div>

            {/* Step 2: Inject Disruptions */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <span className="font-bold text-xs text-slate-800 uppercase tracking-wider block">
                2. Inject Real-Time Disruptions
              </span>

              <div className="space-y-3">
                {/* Trigger A: Inject Critical Incident */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-3 text-xs">
                  <div>
                    <span className="font-bold text-slate-900 block">Inject Critical Incident</span>
                    <span className="text-[11px] text-slate-500">Inject 180 affected, 45 injured in selected zone.</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <select
                      value={targetZone}
                      onChange={(e) => setTargetZone(e.target.value)}
                      className="p-1.5 border border-slate-300 rounded text-xs bg-white"
                    >
                      <option value="Zone C">Zone C</option>
                      <option value="Zone D">Zone D</option>
                      <option value="Zone E">Zone E</option>
                    </select>
                    <button
                      onClick={handleInjectIncident}
                      disabled={isLoading}
                      className="py-1.5 px-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded shadow text-xs"
                    >
                      Inject
                    </button>
                  </div>
                </div>

                {/* Trigger B: Block Road Segment */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-3 text-xs">
                  <div>
                    <span className="font-bold text-slate-900 block">Block Road Segment</span>
                    <span className="text-[11px] text-slate-500">Inundates Mutha riverbank link (Accessibility cut to 15%).</span>
                  </div>
                  <button
                    onClick={handleBlockRoad}
                    disabled={isLoading}
                    className="py-1.5 px-3 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded shadow text-xs whitespace-nowrap"
                  >
                    Block Road
                  </button>
                </div>

                {/* Trigger C: Disable Fleet Unit */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-3 text-xs">
                  <div>
                    <span className="font-bold text-slate-900 block">Disable Fleet Unit</span>
                    <span className="text-[11px] text-slate-500">Simulate vehicle engine failure or comms loss.</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <select
                      value={selectedUnitToDisable}
                      onChange={(e) => setSelectedUnitToDisable(e.target.value)}
                      className="p-1.5 border border-slate-300 rounded text-xs bg-white"
                    >
                      <option value="AMB-07">AMB-07</option>
                      <option value="AMB-02">AMB-02</option>
                      <option value="RESCUE-03">RESCUE-03</option>
                      <option value="BOAT-01">BOAT-01</option>
                    </select>
                    <button
                      onClick={handleDisableResource}
                      disabled={isLoading}
                      className="py-1.5 px-3 bg-slate-800 hover:bg-slate-900 text-white font-bold rounded shadow text-xs"
                    >
                      Disable
                    </button>
                  </div>
                </div>

                {/* Trigger D: Surge Casualties in INC-1047 */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-3 text-xs">
                  <div>
                    <span className="font-bold text-slate-900 block">Surge Casualties (+40 Critical)</span>
                    <span className="text-[11px] text-slate-500">Field triage reports 40 additional victims at INC-1047.</span>
                  </div>
                  <button
                    onClick={handleSurgeCasualties}
                    disabled={isLoading}
                    className="py-1.5 px-3 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded shadow text-xs"
                  >
                    Surge
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Real-Time Event Log & Demonstration Instructions (5 Cols) */}
          <div className="md:col-span-5 space-y-4">
            <div className="bg-slate-900 text-white p-5 rounded-2xl shadow-sm space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                Simulation Telemetry Feed
              </span>

              <div className="h-64 overflow-y-auto space-y-2 pr-1 font-mono text-xs">
                {eventLog.map((log, idx) => (
                  <div key={idx} className="p-2 bg-slate-800/80 rounded border border-slate-700/60 text-slate-300 leading-relaxed">
                    {log}
                  </div>
                ))}
              </div>
            </div>

            {/* Hackathon Demo Walkthrough Card */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-xs space-y-2.5">
              <span className="font-bold text-slate-900 block text-sm">Demo Scenario Protocol:</span>
              <ol className="list-decimal list-inside text-slate-600 space-y-1 leading-relaxed">
                <li>Start with default Flood Scenario in <b>Zone B</b> (INC-1047).</li>
                <li>Click <b>"Inject Critical Incident"</b> in Zone C.</li>
                <li>Click <b>"Block Road Segment"</b> and <b>"Disable AMB-07"</b>.</li>
                <li>Switch to <b>Command Center → Dynamic Reallocation</b> to view the newly computed plan difference.</li>
                <li>Observe the explainability rationale behind each redirected vehicle.</li>
              </ol>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
