# Project Structure

This document outlines the standard folder and file structure for the FinClip Miniprogram Boilerplate. Adhering to this structure promotes consistency and makes projects easier to navigate.

```
.

├── docs/                    # Detailed documentation files (like this one)
├── miniprogram_npm/         # Generated folder for npm components (DO NOT EDIT MANUALLY)
├── src/                     # Source code
├──── components/            # Reusable custom UI components
├──── pages/                 # Application pages (WXML, WXSS, JS, JSON)
├──── services/              # Centralized API call logic
├──── stores/                # MobX state stores
├──── static/                # Static assets (images, fonts)
├──── utils/                 # Utility functions & helpers
├── .editorconfig            # Editor configuration
├── .eslintignore            # ESLint ignore patterns
├── .eslintrc.js             # ESLint configuration
├── .gitignore               # Git ignore patterns
├── .npmrc                   # Local NPM config (contains PAT, Ignored by Git)
├── .prettierignore          # Prettier ignore patterns
├── .prettierrc.js           # Prettier configuration
├── app.js                   # App entry point, lifecycle, global data/methods
├── app.json                 # App configuration (pages, window, subpackages)
├── app.wxss                 # Global styles (minimal)
├── build.js                 # FinClip build & upload script
├── FinClipConf.js           # FinClip extension API definitions (for build tools)
├── fide.project.config.json # FinClip IDE config
├── inject-secrets-dev.js    # Script to fetch DEV secrets
├── inject-secrets-prod.js   # Script to fetch PROD secrets
├── package.json             # Project dependencies and scripts
├── project.config.json      # WeChat DevTools config
├── README.md                # Root project README
└── upload.json              # Configuration for build.js (AppIDs, version)
```

## Folder Descriptions

*   **`components/`**: Contains reusable custom miniprogram components specific to this project (beyond the Design System). Each component should reside in its own sub-folder (e.g., `components/custom-card/`).
*   **`docs/`**: Contains detailed markdown documentation explaining various aspects of the boilerplate and development process.
*   **`miniprogram_npm/`**: **Auto-generated** by the FinClip Studio "Build Npm" command (or equivalent build tool). Contains processed versions of npm packages (like `@credifranco/design-system-mini`) ready for use in the miniprogram. **Do not edit files in this directory manually.** Commit this folder to Git if your build process doesn't automatically generate it in CI/CD.
*   **`pages/`**: Contains all the pages of the miniprogram. Each page resides in its own sub-folder and typically includes four files: `.js` (logic), `.json` (config), `.wxml` (structure), `.wxss` (styles).
*   **`services/`**: Holds modules responsible for communicating with backend APIs. Each service file (e.g., `userService.js`) groups related API calls and uses the configured request utility (`utils/request.js`). See `docs/api-services.md`.
*   **`stores/`**: Contains MobX state stores for managing application state. Includes `configStore.js` for global config and feature-specific stores (e.g., `userStore.js`). See `docs/state-management.md`.
*   **`static/`**: Stores static assets like images, fonts, or JSON data files used directly by the frontend. Sub-folders like `static/images/` are recommended.
*   **`utils/`**: Contains utility modules and helper functions:
    *   `constants.js`: Application-wide constants (API paths, event names, etc.).
    *   `helpers.js`: General helper functions (date formatting, validation, etc.).
    *   `invokeService.js`: Wrappers for FinClip `wx.invoke` extension APIs.
    *   `request.js`: Configured `wx.request` wrapper (handles base URL, auth, API key).
    *   `trackingService.js`: Centralized functions for analytics tracking.

## Key File Descriptions

*   **`app.js`**: The entry point of the miniprogram. Handles application lifecycle events (`onLaunch`, `onShow`, `onError`), global data (minimal), and initializes essential configurations.
*   **`app.json`**: Global configuration for the miniprogram, including pages, subpackages, window appearance, etc.
*   **`app.wxss`**: Global stylesheet. Should contain minimal styles, primarily importing the Design System's base styles.
*   **`build.js`**: Node.js script used for building and deploying the miniprogram package to the FinClip platform via `@finclip/applet-builder-ci`. See `docs/build-deploy.md`.
*   **`FinClipConf.js`**: Defines the custom FinClip extension APIs (`wx.invoke`) used in the project. Primarily used by build tools. See `docs/extension-apis.md`.
*   **`fide.project.config.json`**: Configuration file specific to the FinClip Studio IDE.
*   **`inject-secrets-*.js`**: Scripts to fetch secrets from AWS Secrets Manager and create the `.env` file for deployments. See `docs/build-deploy.md`.
*   **`package.json`**: Defines project metadata, dependencies (runtime and development), and npm scripts.
*   **`project.config.json`**: Configuration file specific to the WeChat Developer Tools.
*   **`README.md`**: The main entry point documentation for the boilerplate.
*   **`upload.json`**: Configuration file read by `build.js` containing environment-specific AppIDs and the version for deployment.
