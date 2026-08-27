import assert from "node:assert/strict";
import { canAccessAdmin } from "../src/lib/permissions.js";

assert.equal(canAccessAdmin(true), true);
assert.equal(canAccessAdmin(false), false);

console.log("permissions test passed");

