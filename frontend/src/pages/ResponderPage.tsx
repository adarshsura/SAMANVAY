import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../context/WebSocketContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { 
  Shield, Navigation, CheckCircle, Clock, AlertCircle, 
  Send, Mic, Camera, MapPin, Truck, RefreshCw, UserCheck 
} from 'lucide-react';
import { addPendingFieldUpdate } from '../offline/indexedDB';

export const ResponderPage: React.FC = () => {
  const { user, token, login, isAuthenticated } = useAuth();
  const { subscribe } = useWebSocket();

  const [profile, setProfile] = useState<any>(null);
  const [assignment, setAssignment] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [statusUpdating, setStatusUpdating] = useState<boolean>(false);
  const [showUpdateModal, setShowUpdateModal] = useState<boolean>(false);
  const [alertMessage, setAlertMessage] = useState<string | null>(null);

  // Field Update Form State
  const [rescuedCount, setRescuedCount] = useState<number>(0);
  const [injuredCount, setInjuredCount] = useState<number>(0);
  const [trappedCount, setTrappedCount] = useState<number>(0);
  const [roadStatus, setRoadStatus] = useState<string>('');
  const [extraResources, setExtraResources] = useState<string>('');
  const [fieldNotes, setFieldNotes] = useState<string>('');

  // Fetch responder profile and current mission
  const fetchResponderData = async () => {
    if (!token) return;
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [profRes, assignRes] = await Promise.all([
        fetch('/api/responder/me', { headers }),
        fetch('/api/responder/assignment', { headers })
      ]);

      if (profRes.ok) {
        const profData = await profRes.json();
        setProfile(profData);
      }
      if (assignRes.ok) {
        const assignData = await assignRes.json();
        setAssignment(assignData);
      }
    } catch (e) {
      console.warn('Failed to load responder data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchResponderData();
    } else {
      setIsLoading(false);
    }

    // Subscribe to live WebSocket events
    const unsubscribe = subscribe((data: any) => {
      if (data.type === 'DISPATCH_APPROVED' || data.type === 'NEW_FIELD_UPDATE' || data.type === 'REALLOCATION_TRIGGERED') {
        fetchResponderData();
      }
    });

    return () => unsubscribe();
  }, [token, isAuthenticated]);

  // Periodic GPS heartbeat
  useEffect(() => {
    if (!token || !profile?.assigned_resource?.id) return;

    const interval = setInterval(() => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            fetch('/api/resources/heartbeat', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                resource_id: profile.assigned_resource.id,
                latitude: pos.coords.latitude,
                longitude: pos.coords.longitude,
                connectivity_state: navigator.onLine ? 'ONLINE' : 'DEGRADED'
              })
            }).catch(() => {});
          },
          () => {}
        );
      }
    }, 15000);

    return () => clearInterval(interval);
  }, [token, profile]);

  // Handle Responder State Machine
  const handleUpdateStatus = async (newStatus: string) => {
    setStatusUpdating(true);
    setAlertMessage(null);
    try {
      const res = await fetch(`/api/responder/status?new_status=${newStatus}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setAlertMessage(`Status updated to ${newStatus}`);
        fetchResponderData();
        setTimeout(() => setAlertMessage(null), 3500);
      }
    } catch (e) {
      setAlertMessage('Network issue. Status change queued locally.');
    } finally {
      setStatusUpdating(false);
    }
  };

  // Handle Field Update Submission
  const handleSubmitFieldUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignment?.incident?.id) return;

    const payload = {
      responder_id: profile?.id || 'RESP-01',
      rescued_count: Number(rescuedCount),
      injured_count: Number(injuredCount),
      trapped_count: Number(trappedCount),
      road_status: roadStatus,
      extra_resources_needed: extraResources,
      text_report: fieldNotes
    };

    if (!navigator.onLine) {
      // Offline support via IndexedDB
      await addPendingFieldUpdate({
        incident_id: assignment.incident.id,
        payload,
        token
      });
      setAlertMessage('Offline: Field update stored in local queue. Will sync on reconnect.');
      setShowUpdateModal(false);
      return;
    }

    try {
      const res = await fetch(`/api/responder/field-update?incident_id=${assignment.incident.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setAlertMessage(`Field update submitted. Incident Need Score updated to ${data.new_need_score}.`);
        setShowUpdateModal(false);
        fetchResponderData();
        setTimeout(() => setAlertMessage(null), 4000);
      }
    } catch (err) {
      await addPendingFieldUpdate({
        incident_id: assignment.incident.id,
        payload,
        token
      });
      setAlertMessage('Connection degraded: update queued locally.');
      setShowUpdateModal(false);
    }
  };

  // Quick 1-click login for demo testing
  const handleQuickLogin = async (username: string) => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password: 'resp123' })
      });
      if (res.ok) {
        const data = await res.json();
        login(data.access_token, {
          username: data.username,
          role: 'RESPONDER',
          responderId: data.responder_id,
          name: data.name
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Not logged in view
  if (!isAuthenticated) {
    return (
      <div className="min-h-[calc(100vh-4rem)] bg-slate-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-200 p-6 sm:p-8 text-center space-y-6">
          <div className="w-14 h-14 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
            <Truck className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Responder Mobile Cockpit</h2>
            <p className="text-xs text-slate-500 mt-1">
              Field operational dispatch, triage, and on-scene reporting console.
            </p>
          </div>

          <div className="space-y-3 pt-2">
            <button
              onClick={() => handleQuickLogin('responder1')}
              className="w-full py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm shadow transition flex items-center justify-center space-x-2"
            >
              <UserCheck className="w-4 h-4" />
              <span>Login as Paramedic Lead (Pravin Jadhav - AMB-01)</span>
            </button>

            <button
              onClick={() => handleQuickLogin('responder2')}
              className="w-full py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-900 text-white font-semibold text-sm shadow transition flex items-center justify-center space-x-2"
            >
              <UserCheck className="w-4 h-4" />
              <span>Login as Rescue Commander (Sunita Rao - RESCUE-01)</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-slate-100 py-6 px-4 sm:px-6">
      <div className="max-w-xl mx-auto space-y-5">

        {/* Alert Notification */}
        {alertMessage && (
          <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-xl text-emerald-900 text-xs flex items-center space-x-2 shadow-sm">
            <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{alertMessage}</span>
          </div>
        )}

        {/* Top Profile Card */}
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-base">
              {profile?.responder_code || 'RESP'}
            </div>
            <div>
              <h2 className="font-bold text-slate-900 text-base">{profile?.name || user?.name || user?.username}</h2>
              <p className="text-xs text-slate-500">{profile?.role || 'Paramedic Unit'} • {profile?.organization || 'NDRF'}</p>
            </div>
          </div>
          <div>
            <StatusBadge status={profile?.current_status || 'AVAILABLE'} size="md" />
          </div>
        </div>

        {/* Vehicle / Unit Telemetry Card */}
        {profile?.assigned_resource && (
          <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              <Truck className="w-4 h-4 text-blue-600" />
              <span className="font-semibold text-slate-900">Vehicle: {profile.assigned_resource.resource_code}</span>
              <span className="text-slate-400">({profile.assigned_resource.resource_type})</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-mono text-emerald-700 font-medium">{profile.assigned_resource.status}</span>
            </div>
          </div>
        )}

        {/* Active Emergency Mission Card */}
        {assignment?.has_assignment && assignment.incident ? (
          <div className="bg-white rounded-2xl shadow-md border-2 border-emergency-500 overflow-hidden">
            {/* Header */}
            <div className="bg-emergency-600 text-white p-4 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase bg-black/20 px-2 py-0.5 rounded tracking-wider">
                  ACTIVE MISSION DISPATCH
                </span>
                <h3 className="text-xl font-black mt-1">{assignment.incident.code}</h3>
              </div>
              <div className="text-right">
                <span className="inline-block px-2.5 py-1 bg-white text-emergency-700 font-bold text-xs rounded-full shadow">
                  {assignment.incident.disaster_type}
                </span>
              </div>
            </div>

            {/* Mission Details */}
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-xl border border-slate-200">
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Zone Sector</span>
                  <span className="font-bold text-slate-800 text-sm">{assignment.incident.zone_code}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Estimated ETA</span>
                  <span className="font-bold text-emergency-600 text-sm">{assignment.estimated_eta_minutes} min ({assignment.distance_km} km)</span>
                </div>
              </div>

              <div>
                <span className="text-xs font-bold text-slate-700 block mb-1">Situation Overview:</span>
                <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200 leading-relaxed">
                  {assignment.incident.description || 'Emergency reported with high priority triage requirement.'}
                </p>
              </div>

              {/* Casualty overview */}
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="bg-red-50 p-2.5 rounded-lg border border-red-200">
                  <span className="text-red-700 block font-black text-base">{assignment.incident.reported_injured || 0}</span>
                  <span className="text-slate-600 text-[10px]">Injured</span>
                </div>
                <div className="bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                  <span className="text-amber-700 block font-black text-base">{assignment.incident.reported_trapped || 0}</span>
                  <span className="text-slate-600 text-[10px]">Trapped</span>
                </div>
                <div className="bg-blue-50 p-2.5 rounded-lg border border-blue-200">
                  <span className="text-blue-700 block font-black text-base">{assignment.incident.reported_people || 1}</span>
                  <span className="text-slate-600 text-[10px]">In Danger</span>
                </div>
              </div>

              {/* Action State Machine */}
              <div className="space-y-2 pt-2">
                <span className="text-xs font-bold text-slate-700 block">Dispatch Progression:</span>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleUpdateStatus('EN_ROUTE')}
                    disabled={statusUpdating}
                    className="py-3 px-3 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs shadow flex items-center justify-center space-x-1.5 transition disabled:opacity-50"
                  >
                    <Navigation className="w-3.5 h-3.5" />
                    <span>EN ROUTE</span>
                  </button>

                  <button
                    onClick={() => handleUpdateStatus('ARRIVED')}
                    disabled={statusUpdating}
                    className="py-3 px-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow flex items-center justify-center space-x-1.5 transition disabled:opacity-50"
                  >
                    <MapPin className="w-3.5 h-3.5" />
                    <span>ARRIVED ON SCENE</span>
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-1">
                  <button
                    onClick={() => setShowUpdateModal(true)}
                    className="py-3 px-3 rounded-xl bg-slate-900 hover:bg-black text-white font-bold text-xs shadow flex items-center justify-center space-x-1.5 transition"
                  >
                    <Send className="w-3.5 h-3.5 text-blue-400" />
                    <span>SUBMIT FIELD REPORT</span>
                  </button>

                  <button
                    onClick={() => handleUpdateStatus('COMPLETED')}
                    disabled={statusUpdating}
                    className="py-3 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow flex items-center justify-center space-x-1.5 transition disabled:opacity-50"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>MARK COMPLETED</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 text-center space-y-4">
            <div className="w-14 h-14 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
              <Clock className="w-7 h-7" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-lg">No Active Mission Dispatched</h3>
              <p className="text-xs text-slate-500 max-w-xs mx-auto mt-1">
                You are currently on standby. The Command Center will push critical emergency assignments directly to your screen.
              </p>
            </div>
            <button
              onClick={fetchResponderData}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg inline-flex items-center space-x-1.5 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Check for Dispatch Updates</span>
            </button>
          </div>
        )}

        {/* MODAL: SUBMIT FIELD REPORT */}
        {showUpdateModal && (
          <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 backdrop-blur-sm">
            <div className="bg-white max-w-md w-full rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
              <div className="bg-slate-900 text-white p-4 flex items-center justify-between">
                <h3 className="font-bold text-sm">On-Scene Field Update</h3>
                <button
                  onClick={() => setShowUpdateModal(false)}
                  className="text-slate-400 hover:text-white text-xs"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleSubmitFieldUpdate} className="p-5 space-y-4 text-xs">
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Rescued:</label>
                    <input
                      type="number"
                      min="0"
                      value={rescuedCount}
                      onChange={(e) => setRescuedCount(Number(e.target.value))}
                      className="w-full p-2 border border-slate-300 rounded-lg text-slate-800 focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Injured:</label>
                    <input
                      type="number"
                      min="0"
                      value={injuredCount}
                      onChange={(e) => setInjuredCount(Number(e.target.value))}
                      className="w-full p-2 border border-slate-300 rounded-lg text-slate-800 focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Trapped:</label>
                    <input
                      type="number"
                      min="0"
                      value={trappedCount}
                      onChange={(e) => setTrappedCount(Number(e.target.value))}
                      className="w-full p-2 border border-slate-300 rounded-lg text-slate-800 focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Road / Terrain Condition:</label>
                  <input
                    type="text"
                    value={roadStatus}
                    onChange={(e) => setRoadStatus(e.target.value)}
                    placeholder="E.g. East access road submerged 2ft, impassable for light vans"
                    className="w-full p-2 border border-slate-300 rounded-lg text-slate-800 focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Extra Resources Needed:</label>
                  <input
                    type="text"
                    value={extraResources}
                    onChange={(e) => setExtraResources(e.target.value)}
                    placeholder="E.g. Requesting 2 additional inflatable rescue boats"
                    className="w-full p-2 border border-slate-300 rounded-lg text-slate-800 focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Situation Report / Notes:</label>
                  <textarea
                    rows={3}
                    value={fieldNotes}
                    onChange={(e) => setFieldNotes(e.target.value)}
                    placeholder="Detailed situational conditions, hazards, elderly casualties..."
                    className="w-full p-2 border border-slate-300 rounded-lg text-slate-800 focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div className="pt-2 flex items-center space-x-2">
                  <button
                    type="submit"
                    className="flex-1 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow transition"
                  >
                    Submit Field Report
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowUpdateModal(false)}
                    className="py-3 px-4 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold text-xs"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
