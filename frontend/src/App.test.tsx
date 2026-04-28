import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "./App";
import { renderWithQueryClient } from "./test/test-utils";

const mockGetWanSources = vi.fn();

vi.mock("./api", async () => {
  const actual = await vi.importActual<typeof import("./api")>("./api");
  return {
    ...actual,
    getWanSources: (...args: unknown[]) => mockGetWanSources(...args),
  };
});

vi.mock("./components/FlatMap", () => ({
  FlatMap: () => <div data-testid="flat-map-mock">Flat map mock</div>,
}));

vi.mock("./components/GlobeMap", () => ({
  GlobeMap: () => <div data-testid="globe-map-mock">Globe map mock</div>,
}));

const dataWithMappablePoint = {
  time_range: "24h" as const,
  total_hits: 1,
  items: [
    {
      source_ip: "8.8.8.8",
      country: "United States",
      country_code: "US",
      region: "California",
      city: "Mountain View",
      latitude: 37.386,
      longitude: -122.084,
      event_count: 1,
      last_seen_at: null,
      last_message: "test",
    },
  ],
  countries: [{ country: "United States", country_code: "US", count: 1 }],
};

describe("App", () => {
  beforeEach(() => {
    mockGetWanSources.mockReset();
  });

  it("shows empty states when there is no data", async () => {
    mockGetWanSources.mockResolvedValue({
      time_range: "24h",
      total_hits: 0,
      items: [],
      countries: [],
    });

    renderWithQueryClient(<App />);

    expect(await screen.findByText("No mappable WAN source IPs are available for this time range.")).toBeInTheDocument();
    expect(screen.getByText("No country data yet.")).toBeInTheDocument();
    expect(screen.getByText("No WAN source IPs have been recorded yet.")).toBeInTheDocument();
  });

  it("falls back to text logo when logo loading fails", async () => {
    mockGetWanSources.mockResolvedValue({
      time_range: "24h",
      total_hits: 0,
      items: [],
      countries: [],
    });

    renderWithQueryClient(<App />);
    const logo = await screen.findAllByAltText("NetAtlas logo");
    fireEvent.error(logo[0]);

    expect(await screen.findByLabelText("NetAtlas logo fallback")).toBeInTheDocument();
  });

  it("refetches when user changes the time range", async () => {
    mockGetWanSources.mockResolvedValue({
      time_range: "24h",
      total_hits: 0,
      items: [],
      countries: [],
    });

    renderWithQueryClient(<App />);
    await screen.findByText("No mappable WAN source IPs are available for this time range.");
    const rangeSelect = screen.getByRole("combobox");
    await userEvent.selectOptions(rangeSelect, "7d");

    await waitFor(() => {
      expect(mockGetWanSources).toHaveBeenCalledWith("7d");
    });
  });

  it("toggles between flat map and globe map views", async () => {
    mockGetWanSources.mockResolvedValue(dataWithMappablePoint);

    renderWithQueryClient(<App />);

    expect(await screen.findByTestId("flat-map-mock")).toBeInTheDocument();
    expect(screen.queryByTestId("globe-map-mock")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("tab", { name: "Globe" }));

    expect(await screen.findByTestId("globe-map-mock")).toBeInTheDocument();
    expect(screen.queryByTestId("flat-map-mock")).not.toBeInTheDocument();
  });
});
