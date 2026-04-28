import { buildPopupContent, escapeHtml, flagFromCountryCode, formatCountryName, formatLocation } from "./app-formatting";
import type { WanSourcePoint } from "./api";

const baseItem: WanSourcePoint = {
  source_ip: "198.51.100.7",
  country: "Germany",
  country_code: "DE",
  region: "Berlin",
  city: "Berlin",
  latitude: 52.52,
  longitude: 13.405,
  event_count: 5,
  last_seen_at: null,
  last_message: null,
};

describe("escapeHtml", () => {
  it("escapes unsafe characters", () => {
    expect(escapeHtml(`<script>alert("x") & 'y'</script>`)).toBe(
      "&lt;script&gt;alert(&quot;x&quot;) &amp; &#39;y&#39;&lt;/script&gt;",
    );
  });
});

describe("flagFromCountryCode", () => {
  it("returns a flag for valid 2-letter codes", () => {
    expect(flagFromCountryCode("us")).toBe("🇺🇸");
  });

  it("returns empty string for invalid or missing code", () => {
    expect(flagFromCountryCode("USA")).toBe("");
    expect(flagFromCountryCode(null)).toBe("");
    expect(flagFromCountryCode(undefined)).toBe("");
  });
});

describe("formatCountryName", () => {
  it("falls back to Unknown when country is missing", () => {
    expect(formatCountryName(null, null)).toBe("Unknown");
  });
});

describe("formatLocation", () => {
  it("builds location from available fields", () => {
    expect(formatLocation(baseItem)).toBe("Berlin, Berlin, 🇩🇪 Germany");
  });

  it("handles partial location data", () => {
    expect(formatLocation({ ...baseItem, city: null, region: null, country: null, country_code: null })).toBe("Unknown");
  });
});

describe("buildPopupContent", () => {
  it("escapes message content to avoid html injection", () => {
    const popup = buildPopupContent({
      ...baseItem,
      source_ip: `<img src=x onerror=alert('xss')>`,
      last_message: `hello <b>world</b>`,
    });

    expect(popup).not.toContain("<img src=x onerror=alert('xss')>");
    expect(popup).toContain("&lt;img src=x onerror=alert(&#39;xss&#39;)&gt;");
    expect(popup).toContain("hello &lt;b&gt;world&lt;/b&gt;");
  });
});
