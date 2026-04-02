/**
 * Client-side location bucket for pricing and UX (no GPS).
 * Country is inferred from the browser timezone where possible.
 */

export type UserLocationBucket = 'japan' | 'india' | 'other';

/** ISO-like country codes used with the pricing API */
const TIMEZONE_TO_COUNTRY: Record<string, string> = {
  'Asia/Tokyo': 'JP',
  'Asia/Osaka': 'JP',
  'Asia/Kolkata': 'IN',
  'Asia/Calcutta': 'IN',
};

export function countryCodeFromBrowserTimezone(): string {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return TIMEZONE_TO_COUNTRY[tz] ?? 'US';
  } catch {
    return 'US';
  }
}

export function locationBucketFromCountryCode(countryCode: string): UserLocationBucket {
  const c = countryCode.toUpperCase();
  if (c === 'JP') return 'japan';
  if (c === 'IN') return 'india';
  return 'other';
}
