/**
 * LightHouse API Client
 * 
 * Unified API client for the LightHouse Disaster API
 * Base URL: https://lighthouse-4gv2.onrender.com
 * 
 * This module provides TypeScript functions to interact with the deployed
 * backend API endpoints. All frontend data should come from this API.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "https://lighthouse-4gv2.onrender.com";

// ============================================================================
// TypeScript Types (from OpenAPI Schema)
// ============================================================================

export interface SourceTweet {
  text: string;
  author: string;
  timestamp: string;
  tweet_id: string;
  engagement: Record<string, unknown>;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  location: string;
  lat: number;
  lng: number;
  severity: string;
  incident_type: string;
  status: string;
  created_at: string;
  tags: string[];
  confidence: number;
  casualties_mentioned: boolean;
  damage_mentioned: boolean;
  needs_help: boolean;
  source_tweets: SourceTweet[];
}

export interface Statistics {
  total_incidents: number;
  active_incidents: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
}

export interface HealthResponse {
  status: string;
  database_status?: string;
  uptime_seconds?: number;
  total_incidents?: number;
}

export interface ApiError {
  detail: string;
}

// ============================================================================
// API Client Functions
// ============================================================================

/**
 * Health check endpoint
 * GET /api/health
 */
export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  
  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get all incidents
 * GET /api/incidents
 */
export async function getIncidents(options?: {
  active_only?: boolean;
  limit?: number;
}): Promise<Incident[]> {
  const params = new URLSearchParams();
  
  if (options?.active_only !== undefined) {
    params.append('active_only', String(options.active_only));
  }
  
  if (options?.limit !== undefined) {
    params.append('limit', String(options.limit));
  }

  const url = params.toString() ? `${API_BASE_URL}/api/incidents?${params}` : `${API_BASE_URL}/api/incidents`;
  const response = await fetch(url);
  
  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get a specific incident by ID
 * GET /api/incidents/{incident_id}
 */
export async function getIncidentById(incidentId: string): Promise<Incident> {
  const response = await fetch(`${API_BASE_URL}/api/incidents/${encodeURIComponent(incidentId)}`);
  
  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get incidents by disaster type
 * GET /api/incidents/type/{incident_type}
 */
export async function getIncidentsByType(incidentType: string): Promise<Incident[]> {
  const response = await fetch(`${API_BASE_URL}/api/incidents/type/${encodeURIComponent(incidentType)}`);
  
  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get nearby incidents
 * GET /api/incidents/nearby
 */
export async function getNearbyIncidents(
  lat: number,
  lng: number,
  radiusKm: number = 100
): Promise<Incident[]> {
  const params = new URLSearchParams({
    lat: String(lat),
    lng: String(lng),
    radius_km: String(radiusKm)
  });

  const response = await fetch(`${API_BASE_URL}/api/incidents/nearby?${params}`);
  
  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get database statistics
 * GET /api/stats
 */
export async function getStats(): Promise<Statistics> {
  const response = await fetch(`${API_BASE_URL}/api/stats`);
  
  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get list of incident types
 * GET /api/incident-types
 */
export async function getIncidentTypes(): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/api/incident-types`);
  
  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get list of severity levels
 * GET /api/severity-levels  
 */
export async function getSeverityLevels(): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/api/severity-levels`);
  
  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

// ============================================================================
// Compatibility Functions (for easier migration)
// ============================================================================

/**
 * Historical incident data structure
 */
export interface HistoricalIncident {
  id: string;
  title?: string;
  description?: string;
  location?: string;
  lat?: number;
  lng?: number;
  severity?: string;
  incident_type?: string;
  status?: string;
  tags?: string[];
  source_tweets?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

export interface HistoricalResponse {
  metadata?: {
    date?: string;
    [key: string]: unknown;
  };
  incidents?: HistoricalIncident[];
}

/**
 * Legacy compatibility function for existing code
 * Maps new Incident type to old IncidentResponse type
 */
export interface IncidentResponse {
  id: string;
  title: string;
  description: string;
  location: string;
  severity: string;
  incident_type: string;
  tags: string[];
  estimated_restoration?: string;
  affected_area?: string;
  created_at: string;
  status: string;
  source_tweets: Array<{
    text: string;
    author: string;
    timestamp: string;
    tweet_id: string;
    engagement?: Record<string, unknown>;
  }>;
  lat?: number;
  lng?: number;
}

/**
 * Convert new Incident type to legacy IncidentResponse type
 */
function convertToLegacyFormat(incident: Incident): IncidentResponse {
  return {
    id: incident.id,
    title: incident.title,
    description: incident.description,
    location: incident.location,
    severity: incident.severity,
    incident_type: incident.incident_type,
    tags: incident.tags,
    created_at: incident.created_at,
    status: incident.status,
    source_tweets: incident.source_tweets.map(tweet => ({
      text: tweet.text,
      author: tweet.author,
      timestamp: tweet.timestamp,
      tweet_id: tweet.tweet_id,
      engagement: tweet.engagement
    })),
    lat: incident.lat,
    lng: incident.lng
  };
}

/**
 * Legacy API class for backward compatibility
 * @deprecated Use individual functions instead
 */
export class IncidentAPI {
  static async getAllIncidents(): Promise<IncidentResponse[]> {
    const incidents = await getIncidents();
    return incidents.map(convertToLegacyFormat);
  }

  static async getIncident(incidentId: string, date?: string): Promise<IncidentResponse> {
    // If a date is provided, attempt to fetch from historical incidents
    if (date) {
      const historical = await IncidentAPI.getHistoryIncidents(date);
      const found = historical.incidents?.find((it: HistoricalIncident) => it.id === incidentId);
      if (!found) {
        throw new Error("Incident not found in historical data");
      }
      
      // Convert historical incident to IncidentResponse format
      const sourceTweets = (found.source_tweets || []).map((t: Record<string, unknown>) => ({
        text: (t.text as string) || "",
        author: (t.author as string) || "",
        timestamp: (t.timestamp as string) || "",
        tweet_id: (t.tweet_id as string) || (t.id as string) || "",
        engagement: (t.engagement as Record<string, unknown>) || {}
      }));

      return {
        id: found.id,
        title: found.title || `${found.incident_type} — ${found.location || ""}`,
        description: found.description || "",
        location: found.location || "",
        severity: found.severity || "unknown",
        incident_type: found.incident_type || "",
        tags: found.tags || [],
        created_at: historical.metadata?.date ? `${historical.metadata.date}T00:00:00Z` : new Date().toISOString(),
        status: found.status || "",
        source_tweets: sourceTweets,
        lat: found.lat,
        lng: found.lng
      };
    }

    const incident = await getIncidentById(incidentId);
    return convertToLegacyFormat(incident);
  }

  /**
   * Get available historical dates
   * Fetches from backend /api/history/dates endpoint
   */
  static async getHistoryDates(): Promise<{ dates: string[] }> {
    const response = await fetch(`${API_BASE_URL}/api/history/dates`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  /**
   * Get historical incidents for a specific date
   * Fetches from backend /api/history/incidents/{date} endpoint
   */
  static async getHistoryIncidents(date: string): Promise<HistoricalResponse> {
    const response = await fetch(`${API_BASE_URL}/api/history/incidents/${encodeURIComponent(date)}`);
    if (!response.ok) {
      let message = `HTTP error! status: ${response.status}`;
      try {
        const data = await response.json();
        if (data?.detail) message = data.detail;
      } catch {
        // ignore
      }
      throw new Error(message);
    }
    return response.json();
  }
}