import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface DisasterMapProps {
  incidents: any[];
  resources: any[];
  infrastructure?: {
    zones?: any[];
    hospitals?: any[];
    shelters?: any[];
    roads?: any[];
  };
  selectedIncidentId?: string | null;
  onSelectIncident?: (incident: any) => void;
  center?: [number, number];
  zoom?: number;
}

export const DisasterMap: React.FC<DisasterMapProps> = ({
  incidents,
  resources,
  infrastructure,
  selectedIncidentId,
  onSelectIncident,
  center = [18.5204, 73.8567],
  zoom = 12
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        zoomControl: true,
        attributionControl: false
      }).setView(center, zoom);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
      }).addTo(map);

      const layerGroup = L.layerGroup().addTo(map);
      layerGroupRef.current = layerGroup;
      mapInstanceRef.current = map;
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update Layers & Markers
  useEffect(() => {
    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;
    if (!map || !layerGroup) return;

    layerGroup.clearLayers();

    // 1. Draw Zones (Circles)
    if (infrastructure?.zones) {
      infrastructure.zones.forEach((z) => {
        const circle = L.circle([z.latitude, z.longitude], {
          radius: (z.radius_km || 3.5) * 1000,
          color: '#64748B',
          weight: 1,
          fillColor: '#94A3B8',
          fillOpacity: 0.07,
          dashArray: '4, 4'
        }).bindTooltip(`<b>${z.code}: ${z.name}</b><br/>Pop: ${z.population?.toLocaleString()}`, {
          permanent: false,
          direction: 'center'
        });
        layerGroup.addLayer(circle);
      });
    }

    // 2. Draw Blocked Roads (Red Polyline)
    if (infrastructure?.roads) {
      infrastructure.roads.forEach((road) => {
        if (road.is_blocked || road.accessibility_pct < 50) {
          const line = L.polyline(
            [
              [road.from_lat, road.from_lon],
              [road.to_lat, road.to_lon]
            ],
            {
              color: '#DC2626',
              weight: 5,
              opacity: 0.85,
              dashArray: '8, 6'
            }
          ).bindPopup(
            `<div class="text-xs">
              <strong class="text-red-700">ROAD IMPASSABLE</strong><br/>
              <b>${road.name}</b><br/>
              Access: ${road.accessibility_pct}%<br/>
              Reason: ${road.block_reason || 'Inundated'}
            </div>`
          );
          layerGroup.addLayer(line);
        }
      });
    }

    // 3. Draw Hospitals (H Icon)
    if (infrastructure?.hospitals) {
      infrastructure.hospitals.forEach((h) => {
        const icon = L.divIcon({
          className: 'custom-hosp-icon',
          html: `<div class="w-6 h-6 rounded-md bg-white border-2 border-blue-600 flex items-center justify-center shadow-md text-blue-600 font-bold text-xs">H</div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });
        const marker = L.marker([h.latitude, h.longitude], { icon }).bindPopup(
          `<div class="text-xs">
            <strong class="text-blue-700">${h.name}</strong><br/>
            Zone: ${h.zone_code}<br/>
            Available Beds: <b>${h.available_beds} / ${h.total_beds}</b><br/>
            Trauma Apex: ${h.trauma_capable ? 'Yes' : 'No'}
          </div>`
        );
        layerGroup.addLayer(marker);
      });
    }

    // 4. Draw Shelters (S Icon)
    if (infrastructure?.shelters) {
      infrastructure.shelters.forEach((s) => {
        const icon = L.divIcon({
          className: 'custom-shelter-icon',
          html: `<div class="w-6 h-6 rounded-md bg-white border-2 border-emerald-600 flex items-center justify-center shadow-md text-emerald-700 font-bold text-xs">S</div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });
        const marker = L.marker([s.latitude, s.longitude], { icon }).bindPopup(
          `<div class="text-xs">
            <strong class="text-emerald-700">${s.name}</strong><br/>
            Capacity: <b>${s.capacity}</b> (Occupancy: ${s.current_occupancy})<br/>
            Zone: ${s.zone_code}
          </div>`
        );
        layerGroup.addLayer(marker);
      });
    }

    // 5. Draw Incidents (Pulsating Priority Markers)
    incidents.forEach((inc) => {
      const isCritical = inc.need_score >= 75 || inc.need_priority === 'CRITICAL';
      const isHigh = inc.need_score >= 60 || inc.need_priority === 'HIGH';
      const isSelected = selectedIncidentId === inc.id;

      const bgColor = isCritical ? 'bg-red-600' : isHigh ? 'bg-amber-500' : 'bg-blue-600';
      const borderColor = isSelected ? 'border-4 border-black' : 'border-2 border-white';
      const pulseHtml = isCritical ? '<span class="absolute -inset-1 rounded-full bg-red-500 animate-ping opacity-75"></span>' : '';

      const icon = L.divIcon({
        className: 'custom-incident-icon',
        html: `
          <div class="relative w-7 h-7 cursor-pointer flex items-center justify-center">
            ${pulseHtml}
            <div class="relative w-7 h-7 rounded-full ${bgColor} ${borderColor} shadow-lg flex items-center justify-center text-white font-bold text-[10px]">
              !
            </div>
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      });

      const marker = L.marker([inc.latitude, inc.longitude], { icon });

      marker.on('click', () => {
        if (onSelectIncident) {
          onSelectIncident(inc);
        }
      });

      marker.bindTooltip(
        `<b>${inc.code} (${inc.disaster_type})</b><br/>Need Score: <b>${inc.need_score}</b> (${inc.need_priority})<br/>People Affected: ${inc.reported_people}`,
        { direction: 'top', offset: [0, -14] }
      );

      layerGroup.addLayer(marker);
    });

    // 6. Draw Emergency Resources (Vehicles)
    resources.forEach((res) => {
      let iconColor = 'bg-slate-700';
      let iconLetter = 'U';

      if (res.resource_type === 'Ambulance') {
        iconColor = 'bg-rose-600';
        iconLetter = '🚑';
      } else if (res.resource_type === 'Rescue Team') {
        iconColor = 'bg-blue-600';
        iconLetter = '🦺';
      } else if (res.resource_type === 'Rescue Boat') {
        iconColor = 'bg-cyan-600';
        iconLetter = '🚤';
      } else if (res.resource_type === 'Fire Unit') {
        iconColor = 'bg-amber-600';
        iconLetter = '🚒';
      } else if (res.resource_type === 'Medical Team') {
        iconColor = 'bg-purple-600';
        iconLetter = '🩺';
      } else if (res.resource_type === 'Relief Supply Unit') {
        iconColor = 'bg-emerald-700';
        iconLetter = '📦';
      }

      // Status indicator ring
      const statusRing = res.status === 'AVAILABLE' 
        ? 'ring-2 ring-emerald-400' 
        : res.status === 'ASSIGNED' || res.status === 'EN_ROUTE'
        ? 'ring-2 ring-amber-400 animate-pulse'
        : 'ring-2 ring-slate-400';

      const icon = L.divIcon({
        className: 'custom-resource-icon',
        html: `
          <div class="w-6 h-6 rounded-full ${iconColor} ${statusRing} shadow flex items-center justify-center text-white text-[11px]">
            ${iconLetter}
          </div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });

      const marker = L.marker([res.latitude, res.longitude], { icon }).bindPopup(
        `<div class="text-xs">
          <strong class="font-bold">${res.resource_code}</strong>: ${res.name}<br/>
          Type: <b>${res.resource_type}</b><br/>
          Status: <b>${res.status}</b><br/>
          Battery: ${res.battery_level}% | Comms: ${res.communication_status}
        </div>`
      );

      layerGroup.addLayer(marker);
    });

  }, [incidents, resources, infrastructure, selectedIncidentId]);

  return (
    <div className="w-full h-full relative rounded-lg overflow-hidden border border-slate-200 shadow-inner">
      <div ref={mapContainerRef} className="w-full h-full min-h-[350px]" />
      
      {/* Map Legend Overlay */}
      <div className="absolute bottom-3 right-3 bg-white/95 backdrop-blur-sm p-2.5 rounded-lg border border-slate-300 shadow-md text-[11px] space-y-1.5 z-[1000] hidden sm:block">
        <div className="font-semibold text-slate-800 text-[11px] mb-1">MAP LEGEND</div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-red-600" />
          <span className="text-slate-700">Critical Incident</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-amber-500" />
          <span className="text-slate-700">High Incident</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs">🚑 🦺 🚤</span>
          <span className="text-slate-700">Emergency Vehicles</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-4 h-1 bg-red-600 border-dashed" />
          <span className="text-slate-700">Blocked / Inundated Road</span>
        </div>
      </div>
    </div>
  );
};
