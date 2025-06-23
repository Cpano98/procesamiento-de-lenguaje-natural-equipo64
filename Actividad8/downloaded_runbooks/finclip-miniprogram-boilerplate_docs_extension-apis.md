# FinClip Extension APIs (`wx.invoke`)

This document details the custom FinClip Extension APIs available in our miniprograms via `wx.invoke`. These APIs provide access to native app functionalities not covered by standard WeChat APIs.

**Usage Pattern:**

It is strongly recommended to use the wrappers provided in `utils/invokeService.js` instead of calling `wx.invoke` directly. The wrappers handle promise conversion and basic error logging.

```javascript
// Example using the wrapper in invokeService.js
import { getAuthToken, amplitudeTrackEvent } from '@/utils/invokeService';

async function exampleUsage() {
  try {
    const token = await getAuthToken();
    console.log('Received Token:', token);

    amplitudeTrackEvent({ name: 'some_event', params: { key: 'value' } });

  } catch (error) {
    console.error("Failed to use extension API:", error);
    // Handle error appropriately
  }
}
```

**API Mocking (FinClip Studio):**

During local development using FinClip Studio, you can mock the responses of these APIs. Use the "Example Success JSON Response" provided below for each API in the Studio's mocking tool. Remember to also test failure cases.

---

## Available APIs

### Authentication & Configuration

**1. `getAuthToken`**

*   **Purpose:** Retrieves the user's current authentication token (e.g., AWS Cognito token) from the native host app.
*   **Parameters:** None
*   **Wrapper:** `invokeService.getAuthToken()`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "getAuthToken:ok",
      "token": "eyJraWQiOiEXAMPLEabc123...",
      "success": true
    }
    ```
*   **Example Failure JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "getAuthToken:fail user not logged in",
      "success": false,
      "error": "User not authenticated"
    }
    ```

**2. `getBaseUrl`**

*   **Purpose:** Retrieves various base URLs for backend services configured in the native host app.
*   **Parameters:** None
*   **Wrapper:** `invokeService.getBaseUrls()`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "getBaseUrl:ok",
      "baseUrl": "https://api.example.com/v1",
      "baseUrlV2": "https://api.example.com/v2",
      "turboBaseUrl": "https://turbo.example.com",
      "baseUrlHyperlane": "https://hyperlane.example.com",
      "success": true
    }
    ```
*   **Example Failure JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "getBaseUrl:fail config not found",
      "success": false
    }
    ```

**3. `getApiKey`**

*   **Purpose:** Retrieves the API key required for backend requests from the native host app.
*   **Parameters:** None
*   **Wrapper:** `invokeService.getApiKey()`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "getApiKey:ok",
      "apiKey": "aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567",
      "success": true
    }
    ```

### User & App Info

**4. `getUser`**

*   **Purpose:** Retrieves information about the currently logged-in user from the native host app.
*   **Parameters:** None
*   **Wrapper:** `invokeService.getUser()`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "getUser:ok",
      "deviceId": "device-uuid-12345",
      "id": "user-uuid-67890",
      "email": "user@example.com",
      "name": "Jane Doe",
      "phoneNumber": "+15551234567",
      "acctId": "account-abc",
      "extAcctId": "external-xyz",
      "success": true
    }
    ```

**5. `getInfo`**

*   **Purpose:** Retrieves information about the device and FinClip runtime environment.
*   **Parameters:** None
*   **Wrapper:** `invokeService.getInfo()`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "getInfo:ok",
      "version": "2.1.0", 
      "env": "production", 
      "width": 375, 
      "height": 812, 
      "safeAreaStatusBar": 44, 
      "safeAreaBottomOffset": 34, 
      "platform": "iOS",
      "model": "iPhone13,4",
      "system": "iOS 15.4.1",
      "success": true
    }
    ```

### Tracking

**6. `amplitudeTrackEvent`**

*   **Purpose:** Sends an event to Amplitude via the native SDK.
*   **Parameters:**
    *   `name` (string, required): The name of the event.
    *   `params` (object, optional): Key-value pairs of event properties.
*   **Wrapper:** `trackingService.trackAmplitude(name, params)` or `invokeService.amplitudeTrackEvent({ name, params })`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "amplitudeTrackEvent:ok",
      "success": true
    }
    ```

**7. `firebaseLogEvent`**

*   **Purpose:** Sends an event to Firebase Analytics via the native SDK.
*   **Parameters:**
    *   `name` (string, required): The name of the event.
    *   `params` (object, optional): Key-value pairs of event properties.
*   **Wrapper:** `trackingService.trackFirebase(name, params)` or `invokeService.firebaseLogEvent({ name, params })`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "firebaseLogEvent:ok",
      "success": true
    }
    ```

**8. `brazeLogEvent`**

*   **Purpose:** Sends an event to Braze via the native SDK.
*   **Parameters:**
    *   `name` (string, required): The name of the event.
    *   `params` (object, optional): Key-value pairs of event properties.
*   **Wrapper:** `trackingService.trackBraze(name, params)` or `invokeService.brazeLogEvent({ name, params })`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "brazeLogEvent:ok",
      "success": true
    }
    ```

**9. `appsFlyerLogEvent`**

*   **Purpose:** Sends an event to AppsFlyer via the native SDK.
*   **Parameters:**
    *   `name` (string, required): The name of the event.
*   **Wrapper:** `trackingService.trackAppsFlyer(name)` or `invokeService.appsFlyerLogEvent({ name })`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "appsFlyerLogEvent:ok",
      "success": true
    }
    ```

**10. `recordError`**

*   **Purpose:** Logs an error (e.g., to Firebase Crashlytics) via the native layer.
*   **Parameters:**
    *   `error` (string, required): The error message or description.
    *   `code` (number, optional): An optional error code.
*   **Wrapper:** `invokeService.recordError(errorMessage, errorCode)`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "recordError:ok",
      "success": true
    }
    ```

### A/B Testing (Apptimize)

**11. `apptimizeTrack`**

*   **Purpose:** Tracks an event in Apptimize.
*   **Parameters:**
    *   `name` (string, required): Event name.
    *   `params` (number, optional): Event value.
*   **Wrapper:** `invokeService.apptimizeTrack({ name, params })`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "apptimizeTrack:ok",
      "success": true
    }
    ```

**12. `apptimizeIsFeatureFlagOn`**

*   **Purpose:** Checks if an Apptimize feature flag is enabled.
*   **Parameters:**
    *   `feature` (string, required): Feature flag name.
*   **Wrapper:** `invokeService.apptimizeIsFeatureFlagOn({ feature })`
*   **Example Success JSON Response (for Mocking - Flag ON):**
    ```json
    {
      "errMsg": "apptimizeIsFeatureFlagOn:ok",
      "data": true,
      "success": true
    }
    ```
*   **Example Success JSON Response (for Mocking - Flag OFF):**
    ```json
    {
      "errMsg": "apptimizeIsFeatureFlagOn:ok",
      "data": false,
      "success": true
    }
    ```

**13. `apptimizeCreateString` / `Integer` / `Double` / `Boolean`**

*   **Purpose:** Retrieves the value of an Apptimize dynamic variable.
*   **Parameters:**
    *   `name` (string, required): Variable name.
    *   `defaultValue` (string/number/boolean, required): Default value if not found or experiment inactive.
*   **Wrappers:** `invokeService.apptimizeCreateString/Integer/Double/Boolean({ name, defaultValue })`
*   **Example Success JSON Response (for Mocking - String):**
    ```json
    {
      "errMsg": "apptimizeCreateString:ok",
      "data": "Variation A Text", 
      "success": true
    }
    ```
    *(Adapt `data` type for Integer, Double, Boolean mocks)*

### Navigation

**14. `openLink`**

*   **Purpose:** Opens a URL, potentially in an external browser or a native webview, handled by the host app.
*   **Parameters:**
    *   `url` (string, required): The URL to open.
*   **Wrapper:** `invokeService.openLink({ url })`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "openLink:ok",
      "success": true
    }
    ```

**15. `redirect`**

*   **Purpose:** Closes the current miniprogram and opens another FinClip miniprogram.
*   **Parameters:**
    *   `id` (string, required): The FinClip App ID of the miniprogram to redirect to.
*   **Wrapper:** `invokeService.redirect({ id })`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "redirect:ok",
      "success": true
    }
    ```

### Sharing

**16. `share`**

*   **Purpose:** Triggers the native OS sharing dialog.
*   **Parameters:**
    *   `textToShare` (string, required): Text content to share.
    *   `linkToShare` (string, required): URL to include in the share.
    *   `eventName` (string, optional): Tracking event name for share completion/cancellation (handled natively).
*   **Wrapper:** `invokeService.share({ textToShare, linkToShare, eventName })`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "share:ok",
      "success": true 
    }
    ```

**17. `callWhatsapp`**

*   **Purpose:** Opens WhatsApp to initiate a chat with a specific number and pre-filled text.
*   **Parameters:**
    *   `phoneNumber` (string, required): Phone number (including country code).
    *   `textTemplate` (string, required): Pre-filled text message.
*   **Wrapper:** `invokeService.callWhatsapp({ phoneNumber, textTemplate })`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "callWhatsapp:ok",
      "success": true
    }
    ```

### Other

**18. `getSignedData`**

*   **Purpose:** Performs a cryptographic signing operation on data, handled by the native layer. (Use case needs clarification).
*   **Parameters:**
    *   `data` (string, optional): The data to be signed (if required by native implementation).
*   **Wrapper:** `invokeService.getSignedData({ data })`
*   **Example Success JSON Response (for Mocking):**
    ```json
    {
      "errMsg": "getSignedData:ok",
      "data": "aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567SignedSignatureExample",
      "success": true
    }
    ```

---
