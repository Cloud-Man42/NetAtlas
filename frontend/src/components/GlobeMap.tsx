import { useEffect, useMemo, useRef, useState } from "react";
import type { ComponentType } from "react";

import type { WanSourcePoint } from "../api";
import { buildPopupContent } from "../app-formatting";

type GlobeMapProps = {
  items: WanSourcePoint[];
  onError: (message: string | null) => void;
};

type GlobePoint = {
  lat: number;
  lng: number;
  size: number;
  color: string;
  label: string;
};

type GlobeComponentProps = {
  globeImageUrl?: string;
  bumpImageUrl?: string;
  backgroundColor?: string;
  pointsData?: GlobePoint[];
  pointLat?: string | ((d: GlobePoint) => number);
  pointLng?: string | ((d: GlobePoint) => number);
  pointAltitude?: string | ((d: GlobePoint) => number);
  pointRadius?: string | ((d: GlobePoint) => number);
  pointColor?: string | ((d: GlobePoint) => string);
  pointLabel?: string | ((d: GlobePoint) => string);
  width?: number;
  height?: number;
  onGlobeReady?: () => void;
};

type GlobeControls = {
  autoRotate: boolean;
  autoRotateSpeed: number;
  enableDamping: boolean;
  dampingFactor: number;
};

type GlobeApi = {
  controls: () => GlobeControls;
};

type GlobeModule = {
  default: ComponentType<GlobeComponentProps>;
};

const EARTH_TEXTURE = "//unpkg.com/three-globe/example/img/earth-blue-marble.jpg";
const EARTH_BUMP = "//unpkg.com/three-globe/example/img/earth-topology.png";

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

function colorForHits(hits: number, maxHits: number) {
  const ratio = maxHits <= 1 ? 0 : clamp((hits - 1) / (maxHits - 1), 0, 1);
  const hue = 210 - ratio * 190;
  const saturation = 90;
  const lightness = 58 - ratio * 18;
  return `hsl(${hue.toFixed(0)} ${saturation}% ${lightness.toFixed(0)}%)`;
}

export function GlobeMap({ items, onError }: GlobeMapProps) {
  const [GlobeComponent, setGlobeComponent] = useState<ComponentType<GlobeComponentProps> | null>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const globeRef = useRef<GlobeApi | null>(null);

  useEffect(() => {
    let cancelled = false;
    onError(null);

    void import("react-globe.gl")
      .then((module: unknown) => {
        if (cancelled) {
          return;
        }
        const resolved = module as GlobeModule;
        setGlobeComponent(() => resolved.default);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          onError(error instanceof Error ? error.message : "Globe failed to load");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [onError]);

  useEffect(() => {
    const container = canvasRef.current;
    if (!container) {
      return;
    }

    const updateSize = () => {
      const rect = container.getBoundingClientRect();
      setSize({
        width: Math.max(280, Math.floor(rect.width)),
        height: Math.max(360, Math.floor(rect.height)),
      });
    };

    updateSize();
    if (typeof ResizeObserver === "undefined") {
      return undefined;
    }

    const observer = new ResizeObserver(updateSize);
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  const points = useMemo(() => {
    if (items.length === 0) {
      return [] as GlobePoint[];
    }
    const maxHits = Math.max(...items.map((item) => item.event_count));
    return items.map((item) => ({
      lat: item.latitude!,
      lng: item.longitude!,
      size: 0.18 + Math.log2(Math.max(1, item.event_count)) * 0.09,
      color: colorForHits(item.event_count, maxHits),
      label: buildPopupContent(item),
    }));
  }, [items]);

  const handleGlobeReady = () => {
    const controls = globeRef.current?.controls();
    if (!controls) {
      return;
    }
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.35;
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
  };

  const GlobeAny = GlobeComponent as ComponentType<Record<string, unknown>> | null;

  return (
    <div ref={canvasRef} className="map-canvas globe-canvas" data-testid="globe-map-canvas">
      {GlobeAny ? (
        <GlobeAny
          // react-globe.gl forwards refs; cast keeps local typing lightweight.
          ref={globeRef as never}
          globeImageUrl={EARTH_TEXTURE}
          bumpImageUrl={EARTH_BUMP}
          backgroundColor="rgba(0,0,0,0)"
          pointsData={points}
          pointLat="lat"
          pointLng="lng"
          pointAltitude={() => 0.11}
          pointRadius="size"
          pointColor="color"
          pointLabel="label"
          width={size.width || undefined}
          height={size.height || undefined}
          onGlobeReady={handleGlobeReady}
        />
      ) : (
        <div className="empty-state map-loading-state">Loading globe...</div>
      )}
    </div>
  );
}
