import { Injectable } from '@angular/core';
import {
  countryCodeFromBrowserTimezone,
  locationBucketFromCountryCode,
  type UserLocationBucket,
} from './user-location';

/**
 * Detects the user's region from their browser timezone.
 * Passes ?country=XX to pricing endpoints so the backend can return
 * the correct currency (Cloudflare may still override on the server).
 *
 * Buckets: Japan, India, or other (default USD on the backend).
 */

@Injectable({ providedIn: 'root' })
export class RegionService {
  readonly countryCode: string = countryCodeFromBrowserTimezone();
  readonly locationBucket: UserLocationBucket = locationBucketFromCountryCode(this.countryCode);
}
