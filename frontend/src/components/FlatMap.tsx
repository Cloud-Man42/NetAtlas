import { useEffect, useRef } from "react";

import type { WanSourcePoint } from "../api";
import { buildPopupContent } from "../app-formatting";

type FlatMapProps = {
  items: WanSourcePoint[];
  onError: (message: string | null) => void;
};

export function FlatMap({ items, onError }: FlatMapProps) {
  const mapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = mapRef.current;
    if (!container || items.length === 0) {
      return;
    }

    let cancelled = false;
    let cleanupMap: (() => void) | undefined;
    onError(null);

    void import("leaflet")
      .then((L) => {
        if (cancelled || !container) {
          return;
        }

        const center: [number, number] = [items[0].latitude!, items[0].longitude!];
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

        const bounds = L.latLngBounds(items.map((item) => [item.latitude!, item.longitude!] as [number, number]));

        items.forEach((item) => {
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

        if (items.length > 1) {
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
          onError(error instanceof Error ? error.message : "Leaflet failed to load");
        }
      });

    return () => {
      cancelled = true;
      cleanupMap?.();
    };
  }, [items, onError]);

  return <div ref={mapRef} className="map-canvas" data-testid="flat-map-canvas" />;
}
