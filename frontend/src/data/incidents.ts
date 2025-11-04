export type Incident = {
  id: string;
  title: string;
  type: "Flood" | "Wildfire" | "Earthquake" | "Storm" | "Avalanche" | "Tornado" | "Landslide"| "Volcano" | "Drought" | "Heatwave" | "Coldwave"; 
  severity: 1 | 2 | 3; 
  radiusKm: number;    
  city: string;
  state?: string;
  lat: number;
  lng: number;
};

export const incidents: Incident[] = [

  { id: "la-us-wf",     title: "Foothill Wildfire",     type: "Wildfire",  severity: 3, radiusKm: 18, city: "Los Angeles", state: "California", lat: 34.0522, lng: -118.2437 },
  { id: "miami-us-st",  title: "Tropical Storm Bands",  type: "Storm",     severity: 2, radiusKm: 16, city: "Miami",       state: "Florida",    lat: 25.7617, lng: -80.1918 },
  { id: "anch-ak-eq",   title: "Shallow Earthquake",    type: "Earthquake",severity: 1, radiusKm:  7, city: "Anchorage",   state: "Alaska",     lat: 61.2181, lng: -149.9003 },
  { id: "cdmx-mx-fl",   title: "Seasonal Flooding",     type: "Flood",     severity: 2, radiusKm: 12, city: "Mexico City",                     lat: 19.4326, lng: -99.1332 },
  { id: "bc-ca-wf",     title: "BC Wildfire Watch",     type: "Wildfire",  severity: 2, radiusKm: 14, city: "Vancouver",                        lat: 49.2827, lng: -123.1207 },

  { id: "sp-br-fl",     title: "Urban Flash Floods",    type: "Flood",     severity: 3, radiusKm: 16, city: "São Paulo",                        lat: -23.5505, lng: -46.6333 },
  { id: "scl-cl-wf",    title: "Hillside Wildfire",     type: "Wildfire",  severity: 2, radiusKm: 12, city: "Santiago",                         lat: -33.4489, lng: -70.6693 },
  { id: "lim-pe-eq",    title: "Offshore Tremor",       type: "Earthquake",severity: 1, radiusKm:  8, city: "Lima",                             lat: -12.0464, lng: -77.0428 },
  { id: "bog-co-st",    title: "Andean Thunderstorms",  type: "Storm",     severity: 2, radiusKm: 13, city: "Bogotá",                           lat: 4.7110,  lng: -74.0721 },

  { id: "par-fr-fl",    title: "Seine Flood Watch",     type: "Flood",     severity: 2, radiusKm: 11, city: "Paris",                            lat: 48.8566, lng: 2.3522 },
  { id: "mad-es-wf",    title: "Outskirts Wildfire",    type: "Wildfire",  severity: 2, radiusKm: 13, city: "Madrid",                           lat: 40.4168, lng: -3.7038 },
  { id: "rom-it-st",    title: "Severe Thunderstorm",   type: "Storm",     severity: 2, radiusKm: 10, city: "Rome",                             lat: 41.9028, lng: 12.4964 },
  { id: "ath-gr-eq",    title: "Aegean Quake",          type: "Earthquake",severity: 2, radiusKm: 10, city: "Athens",                           lat: 37.9838, lng: 23.7275 },

  { id: "lag-ng-fl",    title: "Coastal Flooding",      type: "Flood",     severity: 3, radiusKm: 18, city: "Lagos",                            lat: 6.5244,  lng: 3.3792 },
  { id: "nai-ke-fl",    title: "Flash Flood Alerts",    type: "Flood",     severity: 2, radiusKm: 12, city: "Nairobi",                          lat: -1.2921, lng: 36.8219 },
  { id: "cpt-za-wf",    title: "Mountain Wildfire",     type: "Wildfire",  severity: 3, radiusKm: 17, city: "Cape Town",                         lat: -33.9249, lng: 18.4241 },
  { id: "acc-gh-st",    title: "Atlantic Squalls",      type: "Storm",     severity: 1, radiusKm:  9, city: "Accra",                            lat: 5.6037,  lng: -0.1870 },

  { id: "ist-tr-eq",    title: "Marmara Tremor",        type: "Earthquake",severity: 2, radiusKm: 11, city: "Istanbul",                         lat: 41.0082, lng: 28.9784 },
  { id: "dxb-ae-st",    title: "Desert Storm System",   type: "Storm",     severity: 2, radiusKm: 14, city: "Dubai",                            lat: 25.2048, lng: 55.2708 },

  { id: "mum-in-fl",    title: "Monsoon Flooding",      type: "Flood",     severity: 3, radiusKm: 20, city: "Mumbai",                           lat: 19.0760, lng: 72.8777 },
  { id: "isl-pk-st",    title: "Severe Thunderstorm",   type: "Storm",     severity: 2, radiusKm: 13, city: "Islamabad",                        lat: 33.6844, lng: 73.0479 },
  { id: "dha-bd-fl",    title: "Riverine Flooding",     type: "Flood",     severity: 3, radiusKm: 18, city: "Dhaka",                            lat: 23.8103, lng: 90.4125 },

  { id: "tyo-jp-eq",    title: "Shallow Quake",         type: "Earthquake",severity: 2, radiusKm:  9, city: "Tokyo",                            lat: 35.6762, lng: 139.6503 },
  { id: "sha-cn-st",    title: "Typhoon Outer Bands",   type: "Storm",     severity: 3, radiusKm: 22, city: "Shanghai",                         lat: 31.2304, lng: 121.4737 },
  { id: "hkg-hk-wf",    title: "Country Park Wildfire", type: "Wildfire",  severity: 1, radiusKm:  7, city: "Hong Kong",                        lat: 22.3193, lng: 114.1694 },
  { id: "sel-kr-st",    title: "Summer Squall Line",    type: "Storm",     severity: 2, radiusKm: 12, city: "Seoul",                            lat: 37.5665, lng: 126.9780 },

  { id: "jkt-id-fl",    title: "Monsoon Floods",        type: "Flood",     severity: 3, radiusKm: 19, city: "Jakarta",                          lat: -6.2088, lng: 106.8456 },
  { id: "mnl-ph-st",    title: "Typhoon Rain Bands",    type: "Storm",     severity: 3, radiusKm: 21, city: "Manila",                           lat: 14.5995, lng: 120.9842 },
  { id: "syd-au-wf",    title: "Bushfire Watch",        type: "Wildfire",  severity: 2, radiusKm: 15, city: "Sydney",                           lat: -33.8688, lng: 151.2093 },
  { id: "akl-nz-fl",    title: "Harbor Flood Advisory", type: "Flood",     severity: 2, radiusKm: 12, city: "Auckland",                         lat: -36.8485, lng: 174.7633 },
];
