# SAMANVAY AI (समन्वय AI)
### Faster Help. Smarter Response.
**AI-Powered Disaster Resource Allocation & Coordination Platform**

> **SAMANVAY** is a compassionate emergency lifeline connecting stranded families with heroic first responders during catastrophic floods, fires, and earthquakes. Through one-touch offline SOS beacons and intelligent rescue coordination, it replaces fear with rapid action, delivering critical help fairly and saving lives when every second counts.

SAMANVAY AI is a complete, working, responsive, web-first humanitarian disaster response and resource coordination system. During sudden-onset catastrophes (floods, building collapses, earthquakes, urban fires), information is incomplete, communication channels degrade, and emergency resources are critically limited. SAMANVAY AI bridges this divide by transforming a one-tap citizen emergency beacon into an intelligent, explainable, and mathematically optimal response plan.

---

## 🌟 Core Flow

```
CITIZEN HELP NOW (Zero Login)
      ↓
BROWSER GPS & SPATIAL CLUSTERING (150m, 3min Anti-Duplicate)
      ↓
LOCATION INTELLIGENCE (Zones, Population Exposure, Hospitals, Shelters, Road Accessibility %)
      ↓
AI INCIDENT UNDERSTANDING (Deterministic NLP, Adaptive Skippable Q&A)
      ↓
EXPLAINABLE NEED SCORE (0–100 Weighted Breakdown)
      ↓
RESOURCE DEMAND PREDICTION (Category-wise Minimum & Recommended)
      ↓
GOOGLE OR-TOOLS MILP OPTIMIZATION (Response Time, Travel Distance, Capacity, Minimum Coverage Preservation)
      ↓
COMMAND CENTER HUMAN-IN-THE-LOOP APPROVAL ("APPROVE & DISPATCH")
      ↓
RESPONDER MOBILE COCKPIT (Task Tracking, Step-by-Step Dispatch Transitions)
      ↓
ON-SCENE FIELD TELEMETRY (Casualties, Rescued, Inundated Road Reports)
      ↓
DYNAMIC REALLOCATION (Plan Delta Diff: OLD vs NEW Plan with Transparent Rationale)
```

---

## 🏗️ Production Architecture & Tech Stack

### Frontend
- **Framework**: React 18, TypeScript, Vite
- **Styling**: Tailwind CSS (Professional humanitarian color palette: restrained emergency red, amber warning, operational navy, clean slate background)
- **GIS Mapping**: Leaflet & OpenStreetMap (interactive markers, incident priority pins, emergency vehicle badges, hospital/shelter overlays, blocked road polylines)
- **Offline & PWA**: Progressive Web App manifest (`manifest.json`), custom Service Worker (`sw.js`), native IndexedDB offline operation queue with automatic synchronization on reconnect
- **Speech & Audio**: Web Speech API for voice-to-text incident reporting

### Backend
- **Framework**: Python 3.11, FastAPI (asynchronous endpoints, CORS, Pydantic v2 schemas)
- **Mathematical Optimization**: **Google OR-Tools** (`pywraplp` SCIP/CBC Mixed-Integer Linear Programming solver)
- **Database**: SQLite with spatial Haversine calculation functions (configured for pluggable PostgreSQL / PostGIS migration via connection string)
- **Security & Auth**: JWT (HS256), bcrypt password hashing, Role-Based Access Control (`CITIZEN`, `ADMIN`, `RESPONDER`)
- **Real-Time Communication**: Native WebSocket broadcaster (`/ws`) with auto-reconnection and live telemetry feeds

---

## 🔑 Demo Login Accounts

Citizens **never** require login or account creation to trigger emergency SOS.

For authorities and emergency personnel:
| Role | Username | Password | Profile & Unit |
| :--- | :--- | :--- | :--- |
| **Command Center Admin** | `admin` | `admin123` | Operational Command Center Director |
| **Responder 1 (Paramedic)** | `responder1` | `resp123` | Pravin Jadhav (Lead Paramedic, ALS Ambulance `AMB-01`) |
| **Responder 2 (Rescue Unit)**| `responder2` | `resp123` | Sunita Rao (Rescue Commander, NDRF Squad `RESCUE-01`) |

*Note: The login page includes 1-click preset login buttons for instant demo switching.*

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- **Node.js**: v20.x or higher
- **Python**: 3.11.x
- **Git**

### 2. Backend Installation & Startup
```powershell
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server (Runs on port 8000)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*On initial startup, SQLite automatically creates the schema and seeds 29 realistic emergency fleet units, 5 municipal zones, 5 hospitals, 5 shelters, and the INC-1047 flood scenario.*

### 3. Frontend Installation & Startup
```powershell
# Open a new terminal and navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Vite development server (Runs on port 5173)
npm run dev -- --host 127.0.0.1
```

Access the application in your browser at:
👉 **`http://127.0.0.1:5173/`**

---

## 🌐 Deploy to Vercel

SAMANVAY AI is pre-configured for 1-click fullstack deployment on Vercel using `vercel.json` (Vercel Services architecture):

1. Go to your [Vercel Dashboard](https://vercel.com/new) and click **"Import Project"**.
2. Select the repository: **`adarshsura/SAMANVAY`**.
3. Keep the **Root Directory** as `./` (default).
4. Click **Deploy**. Vercel will build the Vite frontend, mount the FastAPI backend service via `main:app`, and map `/api/*` routes automatically.

---

## 🧪 Automated Testing Suite

SAMANVAY AI includes comprehensive automated pytest tests covering all mathematical and operational rules:

```powershell
cd backend
python -m pytest tests -v
```

### Verified Test Cases:
1. `test_sos_and_clustering.py`:
   - Validates zero-login SOS creation with GPS capture.
   - Verifies duplicate SOS protection (repeated taps merged without duplicate incident rows).
   - Verifies spatial clustering ($\le 150\text{m}$, $\le 180\text{s}$) with confidence increment.
2. `test_need_score_and_demand.py`:
   - Verifies explainable 0–100 Need Score calculation with custom configurable weights.
   - Tests multi-category resource demand prediction across Flood and Fire scenarios.
3. `test_optimizer.py`:
   - Verifies Google OR-Tools MILP constraint formulation (no double-booking, capability matching, travel time minimization).
   - Verifies empirical baseline benchmark generation (Greedy Nearest vs MILP).
4. `test_reallocation.py`:
   - Verifies dynamic reallocation delta diff generation without silent overrides.
5. `test_e2e_flow.py`:
   - Validates the entire 18-step disaster response lifecycle from citizen beacon to incident closure.

---

## 🧠 Core Algorithmic Engines

### 1. Google OR-Tools MILP Formulation
- **Decision Variable**: Binary $x_{r, i} \in \{0, 1\}$ representing assignment of resource $r$ to incident $i$.
- **Objective Function**:
  $$\min \sum_{r \in R} \sum_{i \in I} \Big( 2 \cdot \text{ETA}(r, i) + 1.5 \cdot \text{Dist}(r, i) - 3 \cdot \text{NeedScore}(i) \Big)$$
- **Constraints**:
  1. Each unit assigned to at most one incident: $\sum_{i} x_{r, i} \le 1, \forall r$.
  2. Maximum allocations cannot exceed recommended demand for that category.
  3. Strict capability matching (e.g. Inflatable Swiftwater Boats deployed exclusively for flood rescues; Fire Tenders for fire incidents).
  4. Preserves secondary emergency coverage across surrounding zones.

### 2. Explainable Need Score (0–100)
$$\text{Need Score} = 0.30 \cdot \text{MedSev} + 0.25 \cdot \text{PeopleAff} + 0.20 \cdot \text{UnmetDem} + 0.15 \cdot \text{Inaccess} + 0.10 \cdot \text{Vuln}$$
- Fully transparent and configurable by authorities.
- Every incident card displays a breakdown bar explaining exactly *why* a score is high or critical.

### 3. Dynamic Reallocation
Whenever conditions change (e.g., casualties jump by $+40$, an arterial connector road is inundated, or an ambulance suffers mechanical breakdown):
1. SAMANVAY re-runs the MILP solver across candidate resources.
2. Generates an explicit **OLD PLAN vs NEW PLAN** diff.
3. Provides human-in-the-loop approval before actively rerouting vehicles in transit.

---

## 📱 User Roles & Walkthrough

### 1. Citizen Experience (Zero Login)
- **Step 1**: Open site, tap **🚨 HELP NOW**. Browser immediately captures GPS coordinates.
- **Step 2**: 3-second accidental tap grace screen: click **🚨 CONFIRM HELP**.
- **Step 3**: Instant emergency confirmation card with Incident Code (e.g. `INC-1047`).
- **Step 4 (Optional & Skippable)**: Answer adaptive flood questions (water level, people with you, trapped state) or record audio.

### 2. Command Center Operations
- View live GIS map with real-time fleet telemetry, incident severity pins, and blocked roads.
- Inspect Incident Details: review Location Intelligence (nearest trauma hospital, shelter occupancy, sector road access %).
- Click **"RUN OPTIMIZER"** to trigger Google OR-Tools.
- Click **"APPROVE & DISPATCH"** to lock and assign resources, transitioning them to `ASSIGNED`.

### 3. Responder Mobile Cockpit
- Log in as Paramedic Lead (`responder1`).
- View assigned incident, distance, and task instructions.
- Progress through status transitions: `EN ROUTE` $\rightarrow$ `ARRIVED ON SCENE` $\rightarrow$ `SUBMIT FIELD REPORT` $\rightarrow$ `MARK COMPLETED`.
- Submit field report with actual casualty counts and flooded road notes.

### 4. Disaster Simulation Sandbox
- Start the **Flood Escalation Scenario**.
- Click **"Surge Casualties (+40 Critical)"**, **"Block Road Segment"**, and **"Disable AMB-07"**.
- View the real-time simulation telemetry feed.
- Open **Dynamic Reallocation** to inspect how the optimizer dynamically reallocates units to cover the surge.

---

## 📴 Offline-First & PWA Behavior

- **Service Worker**: Caches application assets, manifest, and offline shell.
- **IndexedDB**: When offline, SOS beacons and responder field reports are stored in local IndexedDB object stores (`pending_sos`, `pending_field_updates`).
- **Auto-Sync**: When network connectivity returns, `syncQueue.ts` automatically flushes pending operations to the backend and triggers re-computation.

---

## 🛡️ Security & Privacy
- Zero citizen credentials or personal data stored unnecessarily.
- Passwords hashed using `bcrypt` with unique salts.
- Admin APIs protected via JWT bearer tokens and RBAC middleware.
- Full audit log recording actor, timestamp, and payload for all critical actions.
