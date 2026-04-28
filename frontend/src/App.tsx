import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getWanSources, type TimeRange } from "./api";
import { buildPopupContent, formatCountryName, formatLocation } from "./app-formatting";

const REFRESH_INTERVAL_MS = 5 * 60 * 1000;
const TIME_RANGES: TimeRange[] = ["1h", "24h", "7d", "30d"];
const NETATLAS_LOGO_PATH = "/assets/netatlas logo.png";
const SPLASH_MINIMUM_MS = 1400;

type BrandMarkProps = {
  className?: string;
  imageClassName?: string;
  fallbackClassName?: string;
};

function BrandMark({ className, imageClassName, fallbackClassName }: BrandMarkProps) {
  const [imageVisible, setImageVisible] = useState(true);

  return imageVisible ? (
    <img
      className={className ?? imageClassName}
      src={NETATLAS_LOGO_PATH}
      alt="NetAtlas logo"
      onError={() => setImageVisible(false)}
    />
  ) : (
    <div className={fallbackClassName ?? className} aria-label="NetAtlas logo fallback">
      <span>NA</span>
    </div>
  );
}

export function App() {
  const [timeRange, setTimeRange] = useState<TimeRange>("24h");
  const [mapError, setMapError] = useState<string | null>(null);
  const [showSplash, setShowSplash] = useState(true);
  const mapRef = useRef<HTMLDivElement | null>(null);

  const query = useQuery({
    queryKey: ["wan-sources", timeRange],
    queryFn: () => getWanSources(timeRange),
    refetchInterval: REFRESH_INTERVAL_MS,
  });

  useEffect(() => {
    const timeoutId = window.setTimeout(() => setShowSplash(false), SPLASH_MINIMUM_MS);
    return () => window.clearTimeout(timeoutId);
  }, []);

  const mappableItems = useMemo(
    () => (query.data?.items ?? []).filter((item) => item.latitude !== null && item.longitude !== null),
    [query.data],
  );

  useEffect(() => {
    const container = mapRef.current;
    if (!container || mappableItems.length === 0) {
      return;
    }

    let cancelled = false;
    let cleanupMap: (() => void) | undefined;
    setMapError(null);

    void import("leaflet")
      .then((L) => {
        if (cancelled || !container) {
          return;
        }

        const center: [number, number] = [mappableItems[0].latitude!, mappableItems[0].longitude!];
        const map = L.map(container, {
          zoomControl: true,
          attributionControl: true,
        });

        cleanupMap = () => {
          map.remove();
        };

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
        }).addTo(map);

        const bounds = L.latLngBounds(
          mappableItems.map((item) => [item.latitude!, item.longitude!] as [number, number]),
        );

        mappableItems.forEach((item) => {
          const marker = L.circleMarker([item.latitude!, item.longitude!], {
            radius: Math.min(18, Math.max(6, 6 + Math.log2(Math.max(1, item.event_count)) * 2)),
            color: "#2563eb",
            fillColor: "#60a5fa",
            fillOpacity: 0.8,
            weight: 2,
          });
          marker.addTo(map);
          marker.bindPopup(buildPopupContent(item));
          marker.bindTooltip(`${item.event_count} hits`, { direction: "top" });
        });

        if (mappableItems.length > 1) {
          map.fitBounds(bounds, { padding: [24, 24] });
        } else {
          map.setView(center, 4);
        }

        requestAnimationFrame(() => {
          map.invalidateSize();
        });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setMapError(error instanceof Error ? error.message : "Leaflet failed to load");
        }
      });

    return () => {
      cancelled = true;
      cleanupMap?.();
    };
  }, [mappableItems]);

  return (
    <div className="app-shell">
      <div className={`splash-screen${showSplash ? " splash-screen--visible" : ""}`} aria-hidden={!showSplash}>
        <div className="splash-card">
          <BrandMark imageClassName="splash-logo" fallbackClassName="splash-logo splash-logo--fallback" />
          <div className="splash-copy">
            <strong>NetAtlas</strong>
            <span>Mapping WAN activity in real time</span>
          </div>
        </div>
      </div>

      <header className="page-header">
        <div className="page-title-group">
          <BrandMark imageClassName="page-logo" fallbackClassName="page-logo page-logo--fallback" />
          <div>
            <h1>NetAtlas</h1>
            <p>Track public source IPs that hit your WAN interface, enrich them with GeoIP, and visualize them on a live atlas.</p>
          </div>
        </div>
        <label className="time-range-control">
          <span>Time range</span>
          <select value={timeRange} onChange={(event) => setTimeRange(event.target.value as TimeRange)}>
            {TIME_RANGES.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </header>

      <section className="stats-grid">
        <div className="stat-card">
          <span>Total hits</span>
          <strong>{query.data?.total_hits ?? 0}</strong>
        </div>
        <div className="stat-card">
          <span>Unique source IPs</span>
          <strong>{query.data?.items.length ?? 0}</strong>
        </div>
        <div className="stat-card">
          <span>Countries seen</span>
          <strong>{query.data?.countries.length ?? 0}</strong>
        </div>
      </section>

      <section className="layout-grid">
        <div className="card map-card">
          <div className="card-header">
            <h2>Map</h2>
          </div>
          {query.isLoading ? (
            <div className="empty-state">Loading map data...</div>
          ) : mapError ? (
            <div className="empty-state">{mapError}</div>
          ) : mappableItems.length === 0 ? (
            <div className="empty-state">No mappable WAN source IPs are available for this time range.</div>
          ) : (
            <div ref={mapRef} className="map-canvas" />
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Countries</h2>
          </div>
          {query.isLoading ? (
            <div className="empty-state">Loading countries...</div>
          ) : (query.data?.countries.length ?? 0) === 0 ? (
            <div className="empty-state">No country data yet.</div>
          ) : (
            <div className="country-list">
              {query.data?.countries.map((country) => (
                <div key={country.country} className="list-row">
                  <strong>{formatCountryName(country.country, country.country_code)}</strong>
                  <span>{country.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <h2>Source IPs</h2>
        </div>
        {query.isLoading ? (
          <div className="empty-state">Loading source IPs...</div>
        ) : (query.data?.items.length ?? 0) === 0 ? (
          <div className="empty-state">No WAN source IPs have been recorded yet.</div>
        ) : (
          <div className="source-list">
            {query.data?.items.map((item) => (
              <div key={item.source_ip} className="source-list-item">
                <div>
                  <strong>{item.source_ip}</strong>
                  <div className="secondary-text">{formatLocation(item)}</div>
                </div>
                <div className="source-list-stats">
                  <strong>{item.event_count}</strong>
                  <span>hits</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
