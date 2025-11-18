/**
 * Legacy Incident type definition for the map widget.
 * This type is used by MapWidget to display incidents on the map.
 *
 * Note: The actual incident data now comes from the backend API at /api/incidents
 * This file only contains the legacy TypeScript type definition for the MapWidget.
 * The main API types are defined in src/api/lighthouseApi.ts
 */
export type Incident = {
  id: string;
  title: string;
  type:
    | "Flood"
    | "Wildfire"
    | "Earthquake"
    | "Hurricane"
    | "Storm"
    | "Avalanche"
    | "Tornado"
    | "Landslide"
    | "Volcano"
    | "Drought"
    | "Heatwave"
    | "Coldwave";
  severity: 1 | 2 | 3;
  radiusKm?: number;
  city?: string;
  state?: string;
  lat: number;
  lng: number;
};

// No longer exporting dummy data - all incidents now come from backend API
// See: backend/main.py /api/incidents endpoint
// See: frontend/src/api/lighthouseApi.ts for API integration
