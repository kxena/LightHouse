// src/HeatmapOverlay.tsx
import { useEffect } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet.heat";

export type HeatPoint = [number, number, number?]; // [lat, lng, intensity 0..1]

type Props = {
  points: HeatPoint[];
  radius?: number;   // px
  blur?: number;     // px
  maxZoom?: number;
  minOpacity?: number; // 0..1
};

export default function HeatmapOverlay({
  points,
  radius = 28,
  blur = 16,
  maxZoom = 12,
  minOpacity = 0.25,
}: Props) {
  const map = useMap();

  useEffect(() => {
    // Red-toned gradient: yellow (low) -> orange -> red -> dark red (high)
    const gradient = {
      0.0: "#fde047", // yellow-300 (lowest)
      0.4: "#fb923c", // orange-400
      0.7: "#ef4444", // red-500
      1.0: "#991b1b", // red-900 (highest)
    };

    const layer = (L as any).heatLayer(points, {
      radius,
      blur,
      maxZoom,
      minOpacity,   // keep faint low-intensity areas visible
      gradient,     // <-- custom red-toned ramp
    });

    layer.addTo(map);
    return () => layer.remove();
  }, [map, points, radius, blur, maxZoom, minOpacity]);

  return null;
}
