// src/MapWidget.tsx
import { useMemo } from "react";
import { MapContainer, TileLayer, Circle, CircleMarker, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Incident } from "../data/incidents";
import HeatmapOverlay, { type HeatPoint } from "./HeatmapOverlay";

type Props = {
  incidents: Incident[];
  heightClass?: string;
  initialCenter?: [number, number];
  initialZoom?: number;
  lockSingleWorld?: boolean;
  focusId?: string;
  onPointClick?: (id: string) => void;
  showRings?: boolean;
  viewMode?: "points" | "heat";
};

function FitOrCenter({ focus, zoom }: { focus?: [number, number]; zoom: number }) {
  const map = useMap();
  if (focus) map.setView(focus, zoom, { animate: false });
  return null;
}

export default function MapWidget({
  incidents,
  heightClass = "h-64",
  initialCenter = [39.5, -98.35],
  initialZoom = 4,
  lockSingleWorld = true,
  focusId,
  onPointClick,
  showRings = false,
  viewMode = "points",
}: Props) {
  const selected = useMemo(
    () => incidents.find((i) => i.id === focusId),
    [incidents, focusId]
  );

  const bounds: [[number, number], [number, number]] = [
    [-85, -180],
    [85, 180],
  ];

  // severity -> heat intensity
  const heatPoints: HeatPoint[] = useMemo(
    () =>
      incidents.map((i) => {
        const intensity = i.severity === 3 ? 1 : i.severity === 2 ? 0.7 : 0.45;
        return [i.lat, i.lng, intensity];
      }),
    [incidents]
  );

  return (
    <div className={`w-full ${heightClass} rounded-2xl overflow-hidden border border-black/10`}>
      <MapContainer
        center={(selected ? [selected.lat, selected.lng] : initialCenter) as [number, number]}
        zoom={selected ? 10 : initialZoom}
        minZoom={2}
        maxZoom={17}
        worldCopyJump={false}
        maxBounds={lockSingleWorld ? bounds : undefined}
        maxBoundsViscosity={lockSingleWorld ? 1.0 : undefined}
        scrollWheelZoom
        style={{ height: "100%", width: "100%" }}
      >
        {/* CartoDB Positron tiles (English-centric labels) */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          detectRetina
          attribution='&copy; OpenStreetMap contributors &copy; CARTO'
        />

        {/* Focus ring only in points mode */}
        {selected && showRings && viewMode === "points" && (
          <>
            <Circle
              center={[selected.lat, selected.lng]}
              radius={selected.radiusKm * 1000}
              pathOptions={{
                color: "rgba(239,68,68,0.9)",
                fillColor: "rgba(239,68,68,0.25)",
                fillOpacity: 0.35,
              }}
            />
            <FitOrCenter focus={[selected.lat, selected.lng]} zoom={11} />
          </>
        )}

        {/* Switchable layer */}
        {viewMode === "heat" ? (
          <HeatmapOverlay points={heatPoints} radius={28} blur={16} maxZoom={12} />
        ) : (
          incidents.map((i) => (
            <CircleMarker
              key={i.id}
              center={[i.lat, i.lng]}
              radius={i.severity === 3 ? 10 : i.severity === 2 ? 7 : 5}
              pathOptions={{
                color:
                  i.severity === 3
                    ? "rgba(239,68,68,1)"
                    : i.severity === 2
                    ? "rgba(234,179,8,1)"
                    : "rgba(34,197,94,1)",
                fillColor:
                  i.severity === 3
                    ? "rgba(239,68,68,0.6)"
                    : i.severity === 2
                    ? "rgba(234,179,8,0.6)"
                    : "rgba(34,197,94,0.6)",
                fillOpacity: 0.8,
              }}
              eventHandlers={{ click: () => onPointClick?.(i.id) }}
            />
          ))
        )}
      </MapContainer>
    </div>
  );
}
