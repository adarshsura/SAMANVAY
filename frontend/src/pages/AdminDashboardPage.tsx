import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../context/WebSocketContext';
import { DisasterMap } from '../components/map/DisasterMap';
import { StatusBadge } from '../components/common/StatusBadge';
import { 
  Activity, AlertOctagon, Truck, Clock, ShieldCheck, 
  RotateCw, CheckCircle2, ChevronRight, X, Sparkles, Filter, 
  Layers, Users, ArrowRightLeft, Database, RefreshCw, GitCompare
} from 'lucide-react';

export const AdminDashboardPage: React.FC = () => {
  const { token, user, login, isAuthenticated } = useAuth();
  const { subscribe } = useWebSocket();

  // Primary active tab
  const [activeTab, setActiveTab] = useState<'operations' | 'optimization' | 'reallocation' | 'resources' | 'verification' | 'benchmark' | 'audit'>('operations');

  // Core data states
  const [summary, setSummary] = useState<any>({
    active_incidents: 0,
    critical_incidents: 0,
    available_resources: 0,
    deployed_resources: 0,
    total_resources: 0,
    unmet_demand: 0,
    average_response_eta_min: 0
  });

  const [incidents, setIncidents] = useState<any[]>([]);
  const [resources, setResources] = useState<any[]>([]);
  const [infrastructure, setInfrastructure] = useState<any>(null);
  const [selectedIncident, setSelectedIncident] = useState<any>(null);
  const [incidentDetail, setIncidentDetail] = useState<any>(null);

  // Optimization & Allocation states
  const [latestAllocation, setLatestAllocation] = useState<any>(null);
  const [reallocationDiff, setReallocationDiff] = useState<any>(null);
  const [baselineBenchmark, setBaselineBenchmark] = useState<any>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // Action / loading states
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Filters
  const [filterDisaster, setFilterDisaster] = useState<string>('ALL');
  const [filterPriority, setFilterPriority] = useState<string>('ALL');

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Fetch all primary dashboard data
  const loadDashboardData = async () => {
    try {
      const [sumRes, incRes, resRes, infraRes, allocRes] = await Promise.all([
        fetch('/api/dashboard/summary'),
        fetch('/api/incidents'),
        fetch('/api/resources'),
        fetch('/api/dashboard/infrastructure'),
        fetch('/api/optimization/latest')
      ]);

      if (sumRes.ok) setSummary(await sumRes.json());
      if (incRes.ok) {
        const incData = await incRes.json();
        setIncidents(incData);
        if (incData.length > 0 && !selectedIncident) {
          setSelectedIncident(incData[0]);
        }
      }
      if (resRes.ok) setResources(await resRes.json());
      if (infraRes.ok) setInfrastructure(await infraRes.json());
      if (allocRes.ok) setLatestAllocation(await allocRes.json());
    } catch (err) {
      console.warn('Dashboard fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch specific incident details
  const loadIncidentDetail = async (id: string) => {
    try {
      const res = await fetch(`/api/incidents/${id}`);
      if (res.ok) {
        setIncidentDetail(await res.json());
      }
    } catch (e) {
      console.warn('Failed to load incident detail', e);
    }
  };

  useEffect(() => {
    loadDashboardData();

    // Subscribe to live WebSocket events for instant real-time updates
    const unsubscribe = subscribe((data: any) => {
      loadDashboardData();
      if (selectedIncident && data.incident_id === selectedIncident.id) {
        loadIncidentDetail(selectedIncident.id);
      }
    });

    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (selectedIncident?.id) {
      loadIncidentDetail(selectedIncident.id);
    }
  }, [selectedIncident]);

  // Load reallocation diff
  const loadReallocationDiff = async () => {
    setActionLoading(true);
    try {
      const res = await fetch('/api/optimization/reallocate?trigger_reason=Casualty+surge+in+Zone+C+and+inundation+in+Zone+B', {
        method: 'POST',
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) }
      });
      if (res.ok) {
        const data = await res.json();
        setReallocationDiff(data);
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Load baseline benchmark
  const loadBaselineBenchmark = async () => {
    setActionLoading(true);
    try {
      const res = await fetch('/api/optimization/baseline-comparison');
      if (res.ok) {
        setBaselineBenchmark(await res.json());
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Load audit logs
  const loadAuditLogs = async () => {
    if (!token) return;
    try {
      const res = await fetch('/api/audit', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setAuditLogs(await res.json());
      }
    } catch (e) {}
  };

  useEffect(() => {
    if (activeTab === 'reallocation') loadReallocationDiff();
    if (activeTab === 'benchmark') loadBaselineBenchmark();
    if (activeTab === 'audit') loadAuditLogs();
  }, [activeTab]);

  // Button Action: Run OR-Tools Optimization
  const handleRunOptimization = async () => {
    setActionLoading(true);
    try {
      const res = await fetch('/api/optimization/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ force_recalculate: true })
      });
      if (res.ok) {
        const data = await res.json();
        setLatestAllocation(data);
        showToast(`OR-Tools MILP Solved: ${data.items.length} units recommended.`);
        loadDashboardData();
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Button Action: Approve & Dispatch
  const handleApproveDispatch = async (allocationId: string) => {
    setActionLoading(true);
    try {
      const res = await fetch(`/api/optimization/${allocationId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ notes: 'Dispatched from Command Center Console' })
      });
      if (res.ok) {
        const data = await res.json();
        showToast(`Dispatch Approved! Assigned units: ${data.dispatched_units.join(', ')}`);
        loadDashboardData();
        if (selectedIncident) loadIncidentDetail(selectedIncident.id);
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Button Action: Close Incident
  const handleCloseIncident = async (incidentId: string) => {
    if (!confirm('Are you sure you want to resolve and close operations for this incident?')) return;
    setActionLoading(true);
    try {
      const res = await fetch(`/api/incidents/${incidentId}/close`, {
        method: 'POST',
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) }
      });
      if (res.ok) {
        showToast('Incident closed and assigned resources released to AVAILABLE.');
        loadDashboardData();
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Button Action: Update Verification Status
  const handleUpdateVerification = async (incidentId: string, status: string) => {
    try {
      const res = await fetch(`/api/incidents/${incidentId}/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ verification_status: status })
      });
      if (res.ok) {
        showToast(`Verification status updated to ${status}`);
        loadDashboardData();
        if (selectedIncident) loadIncidentDetail(selectedIncident.id);
      }
    } catch (e) {}
  };

  // Quick Admin Login
  const handleQuickAdminLogin = async () => {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' })
      });
      if (res.ok) {
        const data = await res.json();
        login(data.access_token, {
          username: data.username,
          role: 'ADMIN',
          name: 'Command Center Director'
        });
        showToast('Logged in as Command Center Director.');
      }
    } catch (e) {}
  };

  // Filtered incidents
  const filteredIncidents = incidents.filter((inc) => {
    if (filterDisaster !== 'ALL' && inc.disaster_type !== filterDisaster) return false;
    if (filterPriority !== 'ALL' && inc.need_priority !== filterPriority) return false;
    return true;
  });

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-slate-100 text-slate-900 flex flex-col">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed top-20 right-6 z-50 p-4 bg-slate-900 text-white rounded-xl shadow-2xl border border-slate-700 flex items-center space-x-2 text-xs">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* TOP OPERATIONAL SUMMARY BAR */}
      <div className="bg-white border-b border-slate-200 py-3.5 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold text-slate-900">Command Center</h1>
            <span className="text-xs font-mono bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-200">
              Pune Metro HQ
            </span>
          </div>

          {/* Quick Metrics Grid */}
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 sm:gap-4 text-center">
            <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
              <span className="text-xs text-slate-500 block">Active Incidents</span>
              <span className="text-lg font-black text-slate-900">{summary.active_incidents}</span>
            </div>
            <div className="bg-red-50 p-2 rounded-lg border border-red-200">
              <span className="text-xs text-red-600 block">Critical</span>
              <span className="text-lg font-black text-red-700">{summary.critical_incidents}</span>
            </div>
            <div className="bg-emerald-50 p-2 rounded-lg border border-emerald-200">
              <span className="text-xs text-emerald-600 block">Available Units</span>
              <span className="text-lg font-black text-emerald-700">{summary.available_resources}</span>
            </div>
            <div className="bg-blue-50 p-2 rounded-lg border border-blue-200">
              <span className="text-xs text-blue-600 block">Deployed</span>
              <span className="text-lg font-black text-blue-700">{summary.deployed_resources}</span>
            </div>
            <div className="bg-amber-50 p-2 rounded-lg border border-amber-200">
              <span className="text-xs text-amber-600 block">Unmet Demand</span>
              <span className="text-lg font-black text-amber-700">{summary.unmet_demand}</span>
            </div>
            <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
              <span className="text-xs text-slate-500 block">Avg Response ETA</span>
              <span className="text-lg font-black text-slate-900">{summary.average_response_eta_min}m</span>
            </div>
          </div>
        </div>
      </div>

      {/* DASHBOARD TAB NAVIGATION */}
      <div className="bg-white border-b border-slate-200 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex items-center space-x-1 sm:space-x-4 overflow-x-auto text-xs sm:text-sm font-semibold py-1">
          <button
            onClick={() => setActiveTab('operations')}
            className={`py-2.5 px-3 border-b-2 transition whitespace-nowrap ${
              activeTab === 'operations' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            Operations & Live Map
          </button>
          <button
            onClick={() => setActiveTab('optimization')}
            className={`py-2.5 px-3 border-b-2 transition whitespace-nowrap flex items-center space-x-1.5 ${
              activeTab === 'optimization' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <span>OR-Tools Allocations</span>
            {latestAllocation?.status === 'RECOMMENDED' && (
              <span className="w-2 h-2 rounded-full bg-amber-500" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('reallocation')}
            className={`py-2.5 px-3 border-b-2 transition whitespace-nowrap flex items-center space-x-1.5 ${
              activeTab === 'reallocation' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <ArrowRightLeft className="w-3.5 h-3.5 text-indigo-600" />
            <span>Dynamic Reallocation</span>
          </button>
          <button
            onClick={() => setActiveTab('resources')}
            className={`py-2.5 px-3 border-b-2 transition whitespace-nowrap ${
              activeTab === 'resources' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            Resource Registry ({resources.length})
          </button>
          <button
            onClick={() => setActiveTab('verification')}
            className={`py-2.5 px-3 border-b-2 transition whitespace-nowrap ${
              activeTab === 'verification' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            Verification Queue
          </button>
          <button
            onClick={() => setActiveTab('benchmark')}
            className={`py-2.5 px-3 border-b-2 transition whitespace-nowrap flex items-center space-x-1.5 ${
              activeTab === 'benchmark' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <GitCompare className="w-3.5 h-3.5 text-emerald-600" />
            <span>Baseline Benchmark</span>
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`py-2.5 px-3 border-b-2 transition whitespace-nowrap ${
              activeTab === 'audit' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            Audit Trail
          </button>
        </div>
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">

        {/* ------------------ TAB 1: OPERATIONS & LIVE MAP ------------------ */}
        {activeTab === 'operations' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full">

            {/* Left Column: Interactive GIS Map & Filters (7 Cols) */}
            <div className="lg:col-span-7 flex flex-col space-y-4">
              <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between gap-3 text-xs">
                <div className="flex items-center space-x-2">
                  <Filter className="w-4 h-4 text-slate-500" />
                  <span className="font-semibold text-slate-700">Filters:</span>
                </div>
                <div className="flex items-center space-x-2">
                  <select
                    value={filterDisaster}
                    onChange={(e) => setFilterDisaster(e.target.value)}
                    className="p-1.5 border border-slate-300 rounded bg-white text-slate-700 text-xs"
                  >
                    <option value="ALL">All Disasters</option>
                    <option value="Flood">Flood</option>
                    <option value="Building Collapse">Building Collapse</option>
                    <option value="Fire">Fire</option>
                    <option value="Earthquake">Earthquake</option>
                  </select>

                  <select
                    value={filterPriority}
                    onChange={(e) => setFilterPriority(e.target.value)}
                    className="p-1.5 border border-slate-300 rounded bg-white text-slate-700 text-xs"
                  >
                    <option value="ALL">All Priorities</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MODERATE">Moderate</option>
                  </select>
                </div>
              </div>

              {/* Leaflet Map Canvas */}
              <div className="h-[480px] bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <DisasterMap
                  incidents={filteredIncidents}
                  resources={resources}
                  infrastructure={infrastructure}
                  selectedIncidentId={selectedIncident?.id}
                  onSelectIncident={(inc) => setSelectedIncident(inc)}
                />
              </div>

              {/* Incidents Table / Selector List */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-slate-900 text-sm">Active Incident Queue ({filteredIncidents.length})</h3>
                  <button
                    onClick={loadDashboardData}
                    className="text-xs text-slate-500 hover:text-slate-800 flex items-center space-x-1"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Refresh</span>
                  </button>
                </div>

                <div className="divide-y divide-slate-100 max-h-56 overflow-y-auto pr-1">
                  {filteredIncidents.map((inc) => (
                    <div
                      key={inc.id}
                      onClick={() => setSelectedIncident(inc)}
                      className={`py-2.5 px-3 rounded-lg cursor-pointer flex items-center justify-between transition ${
                        selectedIncident?.id === inc.id
                          ? 'bg-blue-50 border border-blue-200'
                          : 'hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-2.5 h-2.5 rounded-full bg-red-600" />
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-slate-900 text-xs">{inc.code}</span>
                            <span className="text-[11px] text-slate-500">({inc.zone_code})</span>
                          </div>
                          <div className="text-[11px] text-slate-600">
                            {inc.disaster_type} • Injured: <b>{inc.reported_injured}</b> • Trapped: <b>{inc.reported_trapped}</b>
                          </div>
                        </div>
                      </div>

                      <div className="text-right flex items-center space-x-2">
                        <div>
                          <div className="text-xs font-bold text-red-600">Need: {inc.need_score}</div>
                          <span className="text-[10px] text-slate-400 font-mono">{inc.status}</span>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Live Incident Detail Drawer (5 Cols) */}
            <div className="lg:col-span-5">
              {selectedIncident ? (
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-5">
                  {/* Header */}
                  <div className="border-b border-slate-200 pb-3 flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h2 className="text-lg font-black text-slate-900">{selectedIncident.code}</h2>
                        <StatusBadge status={selectedIncident.need_priority} size="sm" />
                      </div>
                      <span className="text-xs text-slate-500">{selectedIncident.zone_code} • {selectedIncident.disaster_type}</span>
                    </div>
                    <div>
                      <StatusBadge status={selectedIncident.verification_status} size="sm" />
                    </div>
                  </div>

                  {/* Need Score Breakdown Bar */}
                  <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-800">Need Score: {selectedIncident.need_score} / 100</span>
                      <span className="text-slate-500 font-mono">Weighted Algorithm</span>
                    </div>

                    <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden flex">
                      <div style={{ width: `${(selectedIncident.need_breakdown?.medical_severity || 20) * 0.3}%` }} className="bg-red-500 h-full" title="Medical Severity" />
                      <div style={{ width: `${(selectedIncident.need_breakdown?.people_affected || 20) * 0.25}%` }} className="bg-blue-500 h-full" title="People Affected" />
                      <div style={{ width: `${(selectedIncident.need_breakdown?.unmet_demand || 20) * 0.2}%` }} className="bg-amber-500 h-full" title="Unmet Demand" />
                      <div style={{ width: `${(selectedIncident.need_breakdown?.accessibility || 20) * 0.15}%` }} className="bg-slate-500 h-full" title="Inaccessibility" />
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-slate-500">
                      <span>Medical: {selectedIncident.need_breakdown?.medical_severity || 0}</span>
                      <span>Affected: {selectedIncident.need_breakdown?.people_affected || 0}</span>
                      <span>Road Access: {selectedIncident.location_intelligence?.road_accessibility_pct || 85}%</span>
                    </div>
                  </div>

                  {/* Location Intelligence Card */}
                  {selectedIncident.location_intelligence && (
                    <div className="border border-slate-200 rounded-xl p-3 text-xs space-y-1.5 bg-slate-50/50">
                      <span className="font-bold text-slate-800 block text-[11px] uppercase tracking-wider">
                        Location Intelligence (GIS)
                      </span>
                      <div className="grid grid-cols-2 gap-2 text-slate-600">
                        <div>Nearest Hospital: <b>{selectedIncident.location_intelligence.nearest_hospital?.name || 'Sassoon Apex'} ({selectedIncident.location_intelligence.nearest_hospital?.distance_km || 2.1} km)</b></div>
                        <div>Population Exposure: <b>{selectedIncident.location_intelligence.population_exposure}</b></div>
                        <div>Nearest Ambulance: <b>{selectedIncident.location_intelligence.nearest_ambulance_km || 1.2} km</b></div>
                        <div>Hazard Context: <b>{selectedIncident.location_intelligence.hazard_context || 'Riverbank Flooding'}</b></div>
                      </div>
                    </div>
                  )}

                  {/* Predicted Demand vs Assigned */}
                  <div>
                    <span className="font-bold text-slate-800 block text-xs mb-2">Resource Demand vs Allocated:</span>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {selectedIncident.predicted_demand && Object.entries(selectedIncident.predicted_demand).map(([rType, dInfo]: [string, any]) => (
                        <div key={rType} className="p-2 rounded bg-slate-50 border border-slate-200">
                          <span className="font-semibold text-slate-800 block text-[11px]">{rType}</span>
                          <span className="text-slate-500 text-[10px]">
                            Min: <b>{dInfo.min}</b> | Rec: <b>{dInfo.recommended}</b>
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Operational Action Buttons */}
                  <div className="space-y-2 pt-2 border-t border-slate-200">
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={handleRunOptimization}
                        disabled={actionLoading}
                        className="py-2.5 px-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow flex items-center justify-center space-x-1.5 transition disabled:opacity-50"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>RUN OPTIMIZER</span>
                      </button>

                      {latestAllocation && (
                        <button
                          onClick={() => handleApproveDispatch(latestAllocation.id)}
                          disabled={actionLoading}
                          className="py-2.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow flex items-center justify-center space-x-1.5 transition disabled:opacity-50"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>APPROVE & DISPATCH</span>
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => handleUpdateVerification(selectedIncident.id, 'CONFIRMED')}
                        className="py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition"
                      >
                        Confirm Verification
                      </button>
                      <button
                        onClick={() => handleCloseIncident(selectedIncident.id)}
                        disabled={actionLoading}
                        className="py-2 rounded-lg bg-red-50 hover:bg-red-100 text-red-700 font-semibold text-xs border border-red-200 transition"
                      >
                        Close Incident
                      </button>
                    </div>
                  </div>

                  {/* Assigned Fleet & Field Updates */}
                  {incidentDetail?.assigned_resources?.length > 0 && (
                    <div className="pt-2 border-t border-slate-200 text-xs">
                      <span className="font-bold text-slate-800 block mb-1">Dispatched Fleet:</span>
                      <div className="space-y-1">
                        {incidentDetail.assigned_resources.map((r: any, i: number) => (
                          <div key={i} className="p-2 bg-slate-50 rounded border border-slate-200 flex items-center justify-between">
                            <span className="font-semibold text-slate-800">{r.resource_code} ({r.name})</span>
                            <span className="font-mono text-emerald-600 text-[11px]">{r.status} (ETA: {r.eta_minutes}m)</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                </div>
              ) : (
                <div className="p-12 text-center bg-white rounded-xl border border-slate-200 text-slate-400">
                  Select an incident from the map or queue to view detailed intelligence.
                </div>
              )}
            </div>

          </div>
        )}

        {/* ------------------ TAB 2: OR-TOOLS ALLOCATIONS ------------------ */}
        {activeTab === 'optimization' && (
          <div className="space-y-6">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Google OR-Tools MILP Allocations</h2>
                <p className="text-xs text-slate-500">
                  Constraint-based mathematical optimization solving response time, capacity, and coverage reservation.
                </p>
              </div>
              <button
                onClick={handleRunOptimization}
                disabled={actionLoading}
                className="py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-lg shadow flex items-center space-x-2 transition"
              >
                <Sparkles className="w-4 h-4" />
                <span>Re-Calculate Optimization</span>
              </button>
            </div>

            {latestAllocation ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                    <span className="text-slate-500 block">Plan Code</span>
                    <span className="font-mono font-bold text-slate-900 text-sm">{latestAllocation.allocation_code}</span>
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                    <span className="text-slate-500 block">Status</span>
                    <StatusBadge status={latestAllocation.status} size="sm" />
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                    <span className="text-slate-500 block">Total Travel ETA</span>
                    <span className="font-bold text-blue-600 text-sm">{latestAllocation.total_eta_minutes} minutes</span>
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                    <span className="text-slate-500 block">Unmet Demand Count</span>
                    <span className="font-bold text-amber-600 text-sm">{latestAllocation.unmet_demand_count} units</span>
                  </div>
                </div>

                {/* Assignment Cards with Human Explainability */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                  <div className="p-4 border-b border-slate-200 font-bold text-xs text-slate-800 uppercase tracking-wider flex items-center justify-between">
                    <span>Recommended Dispatch Assignments ({latestAllocation.items?.length || 0})</span>
                    {latestAllocation.status === 'RECOMMENDED' && (
                      <button
                        onClick={() => handleApproveDispatch(latestAllocation.id)}
                        disabled={actionLoading}
                        className="py-1.5 px-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded shadow"
                      >
                        Approve All & Dispatch
                      </button>
                    )}
                  </div>

                  <div className="divide-y divide-slate-100">
                    {latestAllocation.items && latestAllocation.items.map((item: any) => (
                      <div key={item.id} className="p-4 space-y-2 text-xs hover:bg-slate-50 transition">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="font-black text-slate-900 text-sm">{item.resource_code}</span>
                            <span className="text-slate-400">({item.resource_type})</span>
                            <span>→</span>
                            <span className="font-bold text-blue-700">{item.incident_code}</span>
                          </div>
                          <div className="font-bold text-emerald-600">
                            ETA: {item.estimated_eta_minutes} min ({item.distance_km} km)
                          </div>
                        </div>

                        {/* Explainable Why Card */}
                        <div className="p-2.5 rounded-lg bg-blue-50/70 border border-blue-200 text-blue-900 text-[11px] leading-relaxed">
                          <span className="font-semibold text-blue-800 block mb-0.5">Why this resource?</span>
                          {item.reason}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white p-12 text-center rounded-xl border border-slate-200 text-slate-500 text-xs">
                No active optimization run found. Click "Re-Calculate Optimization" to formulate an allocation plan.
              </div>
            )}
          </div>
        )}

        {/* ------------------ TAB 3: DYNAMIC REALLOCATION DIFF ------------------ */}
        {activeTab === 'reallocation' && (
          <div className="space-y-6">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                  <ArrowRightLeft className="w-5 h-5 text-indigo-600" />
                  <span>Dynamic Reallocation Diff</span>
                </h2>
                <p className="text-xs text-slate-500">
                  Real-time mathematical comparison between CURRENT PLAN and REVISED PLAN when field dynamics shift.
                </p>
              </div>
              <button
                onClick={loadReallocationDiff}
                disabled={actionLoading}
                className="py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs rounded-lg flex items-center space-x-1.5 transition"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Re-Analyze Delta</span>
              </button>
            </div>

            {reallocationDiff ? (
              <div className="space-y-5">
                {/* Trigger banner */}
                <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-xl text-indigo-950 text-xs flex items-center justify-between">
                  <div>
                    <span className="font-bold text-indigo-900 block text-[11px] uppercase tracking-wider">Dynamic Reallocation Trigger</span>
                    <span className="text-xs">{reallocationDiff.trigger_reason}</span>
                  </div>
                  <span className="font-mono bg-indigo-200/60 text-indigo-900 px-2 py-0.5 rounded text-[11px]">
                    {reallocationDiff.reallocation_id}
                  </span>
                </div>

                {/* Plan Summary Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">CURRENT ACTIVE PLAN</span>
                    <div className="text-sm font-mono text-slate-700">Code: {reallocationDiff.old_plan_summary?.active_allocation_code}</div>
                    <div className="text-xs text-slate-600">Total Units Deployed: <b>{reallocationDiff.old_plan_summary?.total_units_deployed || 0}</b></div>
                    <div className="text-xs text-slate-600">Status: <StatusBadge status={reallocationDiff.old_plan_summary?.status || 'STANDBY'} size="sm" /></div>
                  </div>

                  <div className="bg-white p-5 rounded-xl border border-blue-300 shadow-sm space-y-2">
                    <span className="text-xs font-bold text-blue-600 uppercase tracking-wider block">PROPOSED REALLOCATION PLAN</span>
                    <div className="text-sm font-mono text-blue-900 font-bold">Optimal MILP Re-computed</div>
                    <div className="text-xs text-slate-600">Recommended Units: <b>{reallocationDiff.new_plan_summary?.total_recommended_units}</b></div>
                    <div className="text-xs text-slate-600">Estimated Total ETA: <b>{reallocationDiff.new_plan_summary?.total_eta_minutes} min</b></div>
                  </div>
                </div>

                {/* Delta / Changes Table */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden text-xs">
                  <div className="p-4 border-b border-slate-200 font-bold text-slate-800 uppercase tracking-wider">
                    Reallocation Unit Adjustments ({reallocationDiff.changes?.length || 0})
                  </div>

                  <div className="divide-y divide-slate-100">
                    {reallocationDiff.changes && reallocationDiff.changes.map((chg: any, i: number) => (
                      <div key={i} className="p-4 space-y-1.5 hover:bg-slate-50">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-slate-900 text-sm">{chg.resource_code}</span>
                            <span className="text-slate-400">({chg.resource_type})</span>
                          </div>
                          <div className="text-xs font-semibold text-indigo-700">
                            New ETA: {chg.new_eta_minutes} min
                          </div>
                        </div>

                        <div className="text-xs text-slate-700 flex items-center space-x-2">
                          <span className="line-through text-slate-400">{chg.old_incident_code || 'Standby'}</span>
                          <span>→</span>
                          <span className="font-bold text-blue-600">{chg.new_incident_code}</span>
                        </div>

                        <p className="text-[11px] text-slate-600 bg-slate-50 p-2 rounded border border-slate-200">
                          <b>Reason:</b> {chg.reason}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white p-12 text-center rounded-xl border border-slate-200 text-slate-500 text-xs">
                Analyzing delta across active zones...
              </div>
            )}
          </div>
        )}

        {/* ------------------ TAB 4: RESOURCE REGISTRY ------------------ */}
        {activeTab === 'resources' && (
          <div className="space-y-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Emergency Fleet Registry</h2>
                <p className="text-xs text-slate-500">Live operational status, telemetry, and capabilities of all 29 deployed units.</p>
              </div>
              <button
                onClick={loadDashboardData}
                className="py-1.5 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg"
              >
                Refresh Heartbeats
              </button>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                <thead className="bg-slate-50 font-semibold text-slate-600">
                  <tr>
                    <th className="p-3">Code</th>
                    <th className="p-3">Name & Type</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Capacity</th>
                    <th className="p-3">Battery</th>
                    <th className="p-3">Comms</th>
                    <th className="p-3">Telemetry State</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {resources.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50">
                      <td className="p-3 font-bold font-mono text-slate-900">{r.resource_code}</td>
                      <td className="p-3">
                        <div className="font-semibold text-slate-800">{r.name}</div>
                        <div className="text-[11px] text-slate-400">{r.resource_type}</div>
                      </td>
                      <td className="p-3">
                        <StatusBadge status={r.status} size="sm" />
                      </td>
                      <td className="p-3">{r.capacity} persons</td>
                      <td className="p-3 font-mono">{r.battery_level}%</td>
                      <td className="p-3 font-mono text-[11px]">{r.communication_status}</td>
                      <td className="p-3 text-[11px] text-slate-500">
                        {r.is_stale ? (
                          <span className="text-amber-600 font-semibold">Stale (&gt;120s)</span>
                        ) : (
                          <span className="text-emerald-600">Live Heartbeat</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ------------------ TAB 5: VERIFICATION QUEUE ------------------ */}
        {activeTab === 'verification' && (
          <div className="space-y-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <h2 className="text-lg font-bold text-slate-900">Incident Verification & Anti-Prank Queue</h2>
              <p className="text-xs text-slate-500">
                Multi-signal corroboration analysis evaluating GPS fixes, clustered citizen reports, hazard overlays, and responder verifications.
              </p>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden text-xs">
              <div className="divide-y divide-slate-100">
                {incidents.map((inc) => (
                  <div key={inc.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-slate-900 text-sm">{inc.code}</span>
                        <StatusBadge status={inc.verification_status} size="sm" />
                        <span className="text-slate-400">({inc.zone_code})</span>
                      </div>
                      <p className="text-slate-600">{inc.description || 'Citizen emergency beacon.'}</p>
                      <div className="flex items-center space-x-3 text-[11px] text-slate-500">
                        <span>Confidence: <b>{inc.confidence}%</b></span>
                        <span>•</span>
                        <span>Corroborating Reports: <b>{inc.event_count || 1}</b></span>
                        <span>•</span>
                        <span>Signals: {(inc.verification_signals || []).join(', ')}</span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleUpdateVerification(inc.id, 'CONFIRMED')}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-medium text-xs transition"
                      >
                        Confirm Legitimacy
                      </button>
                      <button
                        onClick={() => handleUpdateVerification(inc.id, 'DISMISSED_AFTER_REVIEW')}
                        className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded font-medium text-xs transition"
                      >
                        Dismiss / False
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ------------------ TAB 6: BASELINE BENCHMARK ------------------ */}
        {activeTab === 'benchmark' && (
          <div className="space-y-6">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <h2 className="text-lg font-bold text-slate-900">Optimization Performance Benchmark</h2>
              <p className="text-xs text-slate-500">
                Empirical quantitative comparison: Baseline Nearest Greedy Resource dispatch vs SAMANVAY Global MILP Optimization.
              </p>
            </div>

            {baselineBenchmark ? (
              <div className="space-y-5 text-xs">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {/* Baseline Card */}
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                    <span className="font-bold text-slate-500 uppercase tracking-wider block">
                      BASELINE (Greedy Nearest Dispatch)
                    </span>
                    <div className="space-y-2 text-slate-700">
                      <div className="flex justify-between py-1 border-b border-slate-100">
                        <span>Average Response ETA:</span>
                        <b className="font-mono text-slate-900">{baselineBenchmark.baseline_greedy.average_eta_minutes} min</b>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-100">
                        <span>Total Travel Distance:</span>
                        <b className="font-mono text-slate-900">{baselineBenchmark.baseline_greedy.total_travel_distance_km} km</b>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-100">
                        <span>Unmet Critical Demand:</span>
                        <b className="font-mono text-amber-600">{baselineBenchmark.baseline_greedy.unmet_demand_count} shortage gaps</b>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-100">
                        <span>Critical Incidents Covered:</span>
                        <b className="font-mono text-slate-900">{baselineBenchmark.baseline_greedy.critical_incidents_covered_percentage}%</b>
                      </div>
                    </div>
                  </div>

                  {/* SAMANVAY MILP Card */}
                  <div className="bg-white p-5 rounded-xl border-2 border-emerald-500 shadow-sm space-y-3">
                    <span className="font-bold text-emerald-700 uppercase tracking-wider block">
                      SAMANVAY AI (Global MILP Optimizer)
                    </span>
                    <div className="space-y-2 text-slate-700">
                      <div className="flex justify-between py-1 border-b border-slate-100">
                        <span>Average Response ETA:</span>
                        <b className="font-mono text-emerald-700">{(baselineBenchmark.samanvay_milp || baselineBenchmark.raahat_milp)?.average_eta_minutes} min</b>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-100">
                        <span>Total Travel Distance:</span>
                        <b className="font-mono text-emerald-700">{(baselineBenchmark.samanvay_milp || baselineBenchmark.raahat_milp)?.total_travel_distance_km} km</b>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-100">
                        <span>Unmet Critical Demand:</span>
                        <b className="font-mono text-emerald-700">{(baselineBenchmark.samanvay_milp || baselineBenchmark.raahat_milp)?.unmet_demand_count} shortage gaps</b>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-100">
                        <span>Critical Incidents Covered:</span>
                        <b className="font-mono text-emerald-700">{(baselineBenchmark.samanvay_milp || baselineBenchmark.raahat_milp)?.critical_incidents_covered_percentage}%</b>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Quantitative Improvements Callout */}
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-950 space-y-1">
                  <span className="font-bold text-emerald-900 block text-xs">Mathematical Advantage Summary:</span>
                  <div>• {baselineBenchmark.improvement_summary?.eta_reduction}</div>
                  <div>• {baselineBenchmark.improvement_summary?.unmet_demand_reduction}</div>
                  <div>• {baselineBenchmark.improvement_summary?.coordination_advantage}</div>
                </div>
              </div>
            ) : (
              <div className="bg-white p-12 text-center rounded-xl border border-slate-200 text-slate-500 text-xs">
                Computing performance metrics...
              </div>
            )}
          </div>
        )}

        {/* ------------------ TAB 7: AUDIT TRAIL ------------------ */}
        {activeTab === 'audit' && (
          <div className="space-y-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900">System Audit Trail</h2>
                <p className="text-xs text-slate-500">Immutable operations log recording dispatch approvals, cancellations, and status transitions.</p>
              </div>
              <button
                onClick={loadAuditLogs}
                className="py-1.5 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg"
              >
                Refresh Log
              </button>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto text-xs">
              <table className="min-w-full divide-y divide-slate-200 text-left">
                <thead className="bg-slate-50 font-semibold text-slate-600">
                  <tr>
                    <th className="p-3">Time</th>
                    <th className="p-3">Action</th>
                    <th className="p-3">Entity</th>
                    <th className="p-3">Actor</th>
                    <th className="p-3">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50">
                      <td className="p-3 font-mono text-slate-500 text-[11px]">
                        {new Date(log.created_at).toLocaleTimeString()}
                      </td>
                      <td className="p-3 font-semibold text-slate-900">{log.action}</td>
                      <td className="p-3 text-slate-600">{log.entity_type} ({log.entity_id.substring(0, 8)})</td>
                      <td className="p-3 text-blue-700 font-medium">{log.performed_by}</td>
                      <td className="p-3 text-slate-500 font-mono text-[11px]">
                        {JSON.stringify(log.details)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
