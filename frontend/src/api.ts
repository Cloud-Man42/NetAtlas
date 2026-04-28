import axios from "axios";

export type TimeRange = "1h" | "24h" | "7d" | "30d";

export type WanSourcePoint = {
  source_ip: string;
  country: string | null;
  country_code: string | null;
  region: string | null;
  city: string | null;
  latitude: number | null;
  longitude: number | null;
  event_count: number;
  last_seen_at: string | null;
  last_message: string | null;
};

export type CountrySummary = {
  country: string;
  country_code: string | null;
  count: number;
};

export type WanSourceResponse = {
  time_range: TimeRange;
  total_hits: number;
  items: WanSourcePoint[];
  countries: CountrySummary[];
};

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
});

export async function getWanSources(timeRange: TimeRange): Promise<WanSourceResponse> {
  const response = await apiClient.get<WanSourceResponse>("/wan-sources", {
    params: { time_range: timeRange },
  });
  return response.data;
}
