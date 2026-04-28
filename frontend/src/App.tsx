import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getWanSources, type TimeRange } from "./api";
import { formatCountryName, formatLocation } from "./app-formatting";
import { FlatMap } from "./components/FlatMap";
import { GlobeMap } from "./components/GlobeMap";

const REFRESH_INTERVAL_MS = 5 * 60 * 1000;
const TIME_RANGES: TimeRange[] = ["1h", "24h", "7d", "30d"];
const NETATLAS_LOGO_PATH = "/assets/netatlas logo.png";
const SPLASH_MINIMUM_MS = 1400;
const MAP_VIEWS = ["flat", "globe"] as const;

type MapView = (typeof MAP_VIEWS)[number];

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
  const [mapView, setMapView] = useState<MapView>("flat");

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
            <div className="map-view-toggle" role="tablist" aria-label="Map view">
              {MAP_VIEWS.map((view) => (
                <button
                  key={view}
                  type="button"
                  role="tab"
                  aria-selected={mapView === view}
                  className={`map-view-toggle__button${mapView === view ? " map-view-toggle__button--active" : ""}`}
                  onClick={() => setMapView(view)}
                >
                  {view === "flat" ? "Flat map" : "Globe"}
                </button>
              ))}
            </div>
          </div>
          {query.isLoading ? (
            <div className="empty-state">Loading map data...</div>
          ) : mapError ? (
            <div className="empty-state">{mapError}</div>
          ) : mappableItems.length === 0 ? (
            <div className="empty-state">No mappable WAN source IPs are available for this time range.</div>
          ) : mapView === "flat" ? (
            <FlatMap items={mappableItems} onError={setMapError} />
          ) : (
            <GlobeMap items={mappableItems} onError={setMapError} />
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
