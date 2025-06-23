# Tracking Service

This document explains how to use the standardized tracking service (`utils/trackingService.js`) to send analytics events to various platforms (Amplitude, Firebase, etc.) via the FinClip native extension APIs.

## Purpose

Using a centralized `trackingService.js` provides several benefits:

1.  **Consistency:** Ensures events are tracked using the same function calls and potentially the same data structures across the application.
2.  **Abstraction:** Hides the underlying `wx.invoke` calls for specific tracking platforms. If a platform changes or is added/removed, updates are localized to `invokeService.js` and potentially `trackingService.js`, minimizing changes in pages/components.
3.  **Simplicity:** Provides simple, named functions (e.g., `trackPageView`, `trackButtonClick`) for common tracking scenarios.
4.  **Maintainability:** Makes it easier to find where specific events are tracked.
5.  **Error Handling:** Basic error handling (logging failures) for the `wx.invoke` calls is included.

## Core Utilities

*   **`utils/trackingService.js`:** Exports functions like `trackAmplitude`, `trackFirebase`, `trackPageView`, etc.
*   **`utils/invokeService.js`:** Contains the actual wrappers (`amplitudeTrackEvent`, `firebaseLogEvent`, etc.) that call `wx.invoke`.
*   **`utils/constants.js`:** Defines constants for event names (`TRACKING_EVENTS`) and common parameter keys (`TRACKING_PARAMS`) to avoid magic strings and ensure consistency.

## How to Use

1.  **Import:** Import the required tracking functions from `@/utils/trackingService` (adjust path if needed) into your Page or Component `.js` file.
2.  **Import Constants:** Import event names and parameter keys from `@/utils/constants` for consistency.
3.  **Call Tracking Functions:** Call the appropriate function at the relevant point in your code (e.g., `onLoad`, event handlers).

**Example: Tracking a Page View**

```javascript
// pages/some-page/some-page.js
import { trackPageView } from '@/utils/trackingService';
import { TRACKING_EVENTS } from '@/utils/constants'; // Event names not strictly needed for trackPageView helper

Page({
  onLoad(options) {
    // Track page view when the page loads
    trackPageView('SomePageName'); // Use a descriptive name for the page
  },
  // ... other page logic
});
```

**Example: Tracking a Button Click**

```javascript
// pages/some-page/some-page.js
import { trackAmplitude, trackFirebase } from '@/utils/trackingService'; // Import specific platform trackers
import { TRACKING_EVENTS, TRACKING_PARAMS } from '@/utils/constants';

Page({
  // ... data, onLoad, etc. ...

  handleButtonClick(event) {
    const itemId = event.currentTarget.dataset.itemId; // Get relevant data

    // Track using specific platform functions
    trackAmplitude(TRACKING_EVENTS.BUTTON_CLICK, {
      [TRACKING_PARAMS.COMPONENT_ID]: 'item_details_button',
      item_id: itemId, // Custom parameter
      [TRACKING_PARAMS.PAGE_NAME]: 'SomePageName' // Add context
    });

    trackFirebase(TRACKING_EVENTS.BUTTON_CLICK, {
       [TRACKING_PARAMS.COMPONENT_ID]: 'item_details_button',
       item_id: itemId
    });

    // Or use a generic helper if you created one in trackingService.js
    // trackButtonClick('item_details_button', { item_id: itemId, page: 'SomePageName' });

    // ... proceed with button action (e.g., navigation) ...
  }
});
```

## Adding New Events

1.  **Define Constants:** Add the new event name and any specific parameter keys to `utils/constants.js` under `TRACKING_EVENTS` and `TRACKING_PARAMS`.
2.  **Track in Code:** Import the constants and use the appropriate `trackAmplitude`, `trackFirebase`, etc., functions from `trackingService.js` in your page/component logic where the event occurs.
3.  **Consider Helpers:** If the event is common (like a specific type of interaction), consider adding a dedicated helper function within `trackingService.js` (similar to `trackPageView`) to simplify its usage.

## Important Notes

*   **Fire-and-Forget:** Tracking calls are generally "fire-and-forget." The `trackingService.js` functions log errors if the underlying `wx.invoke` fails but do not typically block execution or re-throw errors, as tracking failures should usually not break core application functionality.
*   **Platform Specifics:** Be aware that different tracking platforms (Amplitude, Firebase) might have different requirements or best practices for event naming and parameter structures. Consult their respective documentation. The service provides a basic wrapper; complex transformations might need to happen before calling the service function.
*   **Consistency:** Use the defined constants in `utils/constants.js` whenever possible for event names and parameter keys to maintain consistency across the codebase and make data analysis easier.
