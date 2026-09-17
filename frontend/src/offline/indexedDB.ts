// Native IndexedDB helper for offline-first disaster response data
const DB_NAME = 'raahat_offline_db';
const DB_VERSION = 1;

export function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains('pending_sos')) {
        db.createObjectStore('pending_sos', { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains('pending_field_updates')) {
        db.createObjectStore('pending_field_updates', { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains('cached_missions')) {
        db.createObjectStore('cached_missions', { keyPath: 'id' });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function addPendingSos(data: any): Promise<number> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending_sos', 'readwrite');
    const store = tx.objectStore('pending_sos');
    const req = store.add({ ...data, queuedAt: new Date().toISOString() });
    req.onsuccess = () => resolve(req.result as number);
    req.onerror = () => reject(req.error);
  });
}

export async function getPendingSosList(): Promise<any[]> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending_sos', 'readonly');
    const store = tx.objectStore('pending_sos');
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}

export async function removePendingSos(id: number): Promise<void> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending_sos', 'readwrite');
    const store = tx.objectStore('pending_sos');
    const req = store.delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function addPendingFieldUpdate(data: any): Promise<number> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending_field_updates', 'readwrite');
    const store = tx.objectStore('pending_field_updates');
    const req = store.add({ ...data, queuedAt: new Date().toISOString() });
    req.onsuccess = () => resolve(req.result as number);
    req.onerror = () => reject(req.error);
  });
}

export async function getPendingFieldUpdates(): Promise<any[]> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending_field_updates', 'readonly');
    const store = tx.objectStore('pending_field_updates');
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}

export async function removePendingFieldUpdate(id: number): Promise<void> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending_field_updates', 'readwrite');
    const store = tx.objectStore('pending_field_updates');
    const req = store.delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}
