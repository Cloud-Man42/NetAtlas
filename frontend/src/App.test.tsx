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
});
