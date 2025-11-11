/**
 * Incident type definition for the map widget.
 * This type is used by MapWidget to display incidents on the map.
 *
 * Note: The actual incident data now comes from the backend API at /incidents
 * This file only contains the TypeScript type definition.
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
// See: backend/main.py /incidents endpoint
// See: frontend/src/services/incidentAPI.ts for API integration
