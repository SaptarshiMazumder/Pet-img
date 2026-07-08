// ---------------------------------------------------------------------------
// Site-wide feature flags & commerce config
// ---------------------------------------------------------------------------
//
// PRINTS_ENABLED gates every physical-print (framed portrait) surface in the UI.
// It is set to `false` while the site is under Dodo Payments review: Dodo is a
// Merchant of Record for DIGITAL goods only, and physical goods are a prohibited
// category. All print code is kept intact and simply hidden — flip this to `true`
// to restore prints once a separate non-Dodo rail (Cashfree / PayPal) is live.
export const PRINTS_ENABLED = false;
