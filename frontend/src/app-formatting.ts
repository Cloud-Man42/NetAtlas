import type { WanSourcePoint } from "./api";

export function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function flagFromCountryCode(countryCode: string | null | undefined) {
  if (!countryCode || countryCode.length !== 2) {
    return "";
  }

  return countryCode
    .toUpperCase()
    .split("")
    .map((char) => String.fromCodePoint(127397 + char.charCodeAt(0)))
    .join("");
}

export function formatCountryName(country: string | null | undefined, countryCode: string | null | undefined) {
  const label = country || "Unknown";
  const flag = flagFromCountryCode(countryCode);
  return flag ? `${flag} ${label}` : label;
}

export function formatLocation(item: WanSourcePoint) {
  const parts = [item.city, item.region].filter(Boolean);
  parts.push(formatCountryName(item.country, item.country_code));
  return parts.join(", ") || "Unknown location";
}

export function buildPopupContent(item: WanSourcePoint) {
  const lines = [
    `<strong>${escapeHtml(item.source_ip)}</strong>`,
    escapeHtml(formatLocation(item)),
    `Hits: ${item.event_count}`,
  ];

  if (item.last_message) {
    lines.push(`Last message: ${escapeHtml(item.last_message)}`);
  }

  return `<div style="color:#10161d;max-width:280px">${lines.join("<br/>")}</div>`;
}
