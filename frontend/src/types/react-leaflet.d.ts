// src/types/react-leaflet.d.ts
// Loosen React-Leaflet prop typing to avoid TS errors across minor version mismatches.
declare module "react-leaflet" {
  import * as React from "react";
  export const MapContainer: React.ComponentType<any>;
  export const TileLayer: React.ComponentType<any>;
  export const Circle: React.ComponentType<any>;
  export const CircleMarker: React.ComponentType<any>;
  export function useMap(): any;
}
