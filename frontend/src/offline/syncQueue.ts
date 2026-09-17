import {
  getPendingSosList,
  removePendingSos,
  getPendingFieldUpdates,
  removePendingFieldUpdate
} from './indexedDB';

export async function processSyncQueue(): Promise<{ syncedSos: number; syncedUpdates: number }> {
  if (!navigator.onLine) {
    return { syncedSos: 0, syncedUpdates: 0 };
  }

  let syncedSos = 0;
  let syncedUpdates = 0;

  // 1. Sync Pending SOS
  const pendingSos = await getPendingSosList();
  for (const item of pendingSos) {
    try {
      const res = await fetch('/api/sos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: item.session_id,
          latitude: item.latitude,
          longitude: item.longitude,
          accuracy: item.accuracy
        })
      });
      if (res.ok) {
        await removePendingSos(item.id);
        syncedSos++;
      }
    } catch (err) {
      console.warn('Failed to sync offline SOS item', item, err);
    }
  }

  // 2. Sync Pending Field Updates
  const pendingUpdates = await getPendingFieldUpdates();
  for (const item of pendingUpdates) {
    try {
      const res = await fetch(`/api/responder/field-update?incident_id=${item.incident_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(item.token ? { Authorization: `Bearer ${item.token}` } : {})
        },
        body: JSON.stringify(item.payload)
      });
      if (res.ok) {
        await removePendingFieldUpdate(item.id);
        syncedUpdates++;
      }
    } catch (err) {
      console.warn('Failed to sync offline field update', item, err);
    }
  }

  return { syncedSos, syncedUpdates };
}
