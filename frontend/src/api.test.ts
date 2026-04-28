import axios from "axios";

import { getWanSources } from "./api";

const { mockGet } = vi.hoisted(() => ({ mockGet: vi.fn() }));

vi.mock("axios", () => ({
  default: {
    create: vi.fn(() => ({
      get: mockGet,
    })),
  },
}));

describe("getWanSources", () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it("requests wan sources with the selected time range", async () => {
    const payload = { time_range: "24h", total_hits: 1, items: [], countries: [] };
    mockGet.mockResolvedValue({ data: payload });

    await expect(getWanSources("24h")).resolves.toEqual(payload);
    expect(mockGet).toHaveBeenCalledWith("/wan-sources", {
      params: { time_range: "24h" },
    });
  });

  it("propagates request failures", async () => {
    const error = new Error("network down");
    mockGet.mockRejectedValue(error);

    await expect(getWanSources("7d")).rejects.toThrow("network down");
  });

  it("creates axios client once", () => {
    expect(axios.create).toHaveBeenCalledTimes(1);
  });
});
