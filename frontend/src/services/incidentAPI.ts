const API_BASE_URL = "http://localhost:8000";

export interface Tweet {
  text: string;
  author: string;
  timestamp: string;
  tweet_id: string;
  engagement?: {
    likes?: number;
    retweets?: number;
    replies?: number;
  };
}

export interface TweetAnalysisResult {
  tweet: Tweet;
  is_disaster_related: boolean;
  incident_type?: string;
  severity?: "low" | "medium" | "high" | "critical";
  location?: string;
  key_entities: string[];
  confidence_score?: number;
}

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
  source_tweets: Tweet[];
  // Optional geocoding (if backend provides)
  lat?: number;
  lng?: number;
}

export class IncidentAPI {
  static async analyzeTweet(tweetAnalysis: TweetAnalysisResult): Promise<{
    message: string;
    incident_created: boolean;
    incident_id?: string;
    confidence_score?: number;
  }> {
    const response = await fetch(`${API_BASE_URL}/analyze-tweet`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(tweetAnalysis),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  static async getAllIncidents(): Promise<IncidentResponse[]> {
    const response = await fetch(`${API_BASE_URL}/incidents`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  static async getIncident(
    incidentId: string,
    date?: string
  ): Promise<IncidentResponse> {
    // If a date is provided, attempt to fetch from historical incidents and find by id
    if (date) {
      const res = await IncidentAPI.getHistoryIncidents(date);
      const incidents = res.incidents || [];
      const found = incidents.find((it: any) => it.id === incidentId);
      if (!found) {
        throw new Error("Incident not found in historical data");
      }

      // Normalize historical incident into IncidentResponse shape
      const source_tweets = (found.source_tweets || []).map((t: any) => ({
        text: t.text || "",
        author: t.author || "",
        timestamp: t.timestamp || "",
        tweet_id: t.tweet_id || t.id || "",
      }));

      const incident: IncidentResponse = {
        id: found.id,
        title: (found.incident_type
          ? `${found.incident_type} — ${found.location || ""}`
          : found.description || found.id) as string,
        description: (found.description as string) || "",
        location: (found.location as string) || "",
        severity: (found.severity as string) || "unknown",
        incident_type: (found.incident_type as string) || "",
        tags: (found.tags as string[]) || [],
        estimated_restoration:
          (found.estimated_restoration as string) || undefined,
        affected_area: (found.affected_area as string) || undefined,
        created_at:
          res.metadata && res.metadata.date
            ? `${res.metadata.date}T00:00:00Z`
            : new Date().toISOString(),
        status: (found.status as string) || "",
        source_tweets,
        lat: typeof found.lat === "number" ? found.lat : undefined,
        lng: typeof found.lng === "number" ? found.lng : undefined,
      };

      return incident;
    }

    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}`);

    if (!response.ok) {
      // Try to parse the error body for FastAPI { detail }
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

  static async getHistoryDates(): Promise<{ dates: string[] }> {
    const response = await fetch(`${API_BASE_URL}/history/dates`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  static async getHistoryIncidents(date: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/history/incidents/${date}`);
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

  static async updateIncidentStatus(
    incidentId: string,
    status: string
  ): Promise<IncidentResponse> {
    const response = await fetch(
      `${API_BASE_URL}/incidents/${incidentId}/status`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status }),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  static async addTweetToIncident(
    incidentId: string,
    tweet: Tweet
  ): Promise<{ message: string; total_tweets: number }> {
    const response = await fetch(
      `${API_BASE_URL}/incidents/${incidentId}/add-tweet`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(tweet),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
}
