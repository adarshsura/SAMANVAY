import React, { useState, useEffect } from 'react';
import { WifiOff, RefreshCw, CheckCircle2 } from 'lucide-react';
import { processSyncQueue } from '../../offline/syncQueue';
import { getPendingSosList, getPendingFieldUpdates } from '../../offline/indexedDB';

export const OfflineBanner: React.FC = () => {
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const checkPending = async () => {
    try {
      const sos = await getPendingSosList();
      const updates = await getPendingFieldUpdates();
      setPendingCount(sos.length + updates.length);
    } catch (e) {
      // IndexedDB might not be available in some private windows
    }
  };

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      handleSync();
    };
    const handleOffline = () => {
      setIsOnline(false);
      checkPending();
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    const interval = setInterval(checkPending, 5000);
    checkPending();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, []);

  const handleSync = async () => {
    if (!navigator.onLine) return;
    setIsSyncing(true);
    setSyncMessage(null);
    try {
      const { syncedSos, syncedUpdates } = await processSyncQueue();
      await checkPending();
      if (syncedSos > 0 || syncedUpdates > 0) {
        setSyncMessage(`Synced ${syncedSos} offline SOS and ${syncedUpdates} field updates.`);
        setTimeout(() => setSyncMessage(null), 4000);
      }
    } finally {
      setIsSyncing(false);
    }
  };

  if (isOnline && pendingCount === 0 && !syncMessage) {
    return null;
  }

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-xs sm:text-sm text-amber-900 flex items-center justify-between z-40 relative">
      <div className="flex items-center space-x-2">
        {!isOnline ? (
          <>
            <WifiOff className="w-4 h-4 text-amber-600 animate-pulse" />
            <span className="font-semibold">Offline Mode Active.</span>
            <span className="text-amber-700 hidden sm:inline">
              Actions are securely preserved in IndexedDB queue and will synchronize automatically when connection returns.
            </span>
          </>
        ) : syncMessage ? (
          <>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span className="text-emerald-800 font-medium">{syncMessage}</span>
          </>
        ) : (
          <span>{pendingCount} unsynced operation{pendingCount > 1 ? 's' : ''} queued locally.</span>
        )}
      </div>

      {pendingCount > 0 && isOnline && (
        <button
          onClick={handleSync}
          disabled={isSyncing}
          className="ml-3 px-2.5 py-1 bg-amber-600 hover:bg-amber-700 text-white font-medium rounded text-xs flex items-center space-x-1 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
          <span>{isSyncing ? 'Syncing...' : 'Sync Now'}</span>
        </button>
      )}
    </div>
  );
};
