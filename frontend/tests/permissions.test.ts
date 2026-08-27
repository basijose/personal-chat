import { describe, expect, it } from "vitest";
import { canAccessAdmin } from "../src/lib/permissions";

describe("permissions", () => {
  it("only allows superadmins into admin", () => {
    expect(canAccessAdmin(true)).toBe(true);
    expect(canAccessAdmin(false)).toBe(false);
  });
});
