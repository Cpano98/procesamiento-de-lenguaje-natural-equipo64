# Build & Deployment Process

This document explains how to build the miniprogram package and deploy it to the FinClip platform using the provided scripts. The process relies on FinClip's command-line tools (`@finclip/applet-builder-ci`) and AWS Secrets Manager for handling sensitive credentials.

## Overview

The deployment process involves these key components:

1.  **AWS Secrets Manager:** Stores sensitive information like the FinClip `MPOpenAPISecret` and `MPServerUrl`.
2.  **`inject-secrets-*.js` Scripts:** Node.js scripts that fetch secrets from AWS Secrets Manager for a specific environment (dev/prod) and write them into a temporary `.env` file.
3.  **`.env` File:** A temporary file (ignored by Git) created by the inject scripts, containing the fetched secrets.
4.  **`dotenv` Package:** Used by `build.js` to load variables from the `.env` file into the script's environment.
5.  **`upload.json`:** Configuration file specifying the target FinClip App ID (`appId`) and the `version` number for the deployment environment (dev/prod).
6.  **`build.js` Script:** The main Node.js script that:
    *   Loads configuration from `.env` and `upload.json`.
    *   Validates required configuration.
    *   Configures `.npmrc` for private package installation (though usually done manually beforehand).
    *   Installs dependencies (`npm install`).
    *   Uses `@finclip/applet-builder-ci` to:
        *   Package npm dependencies (`packNpm`).
        *   Build the miniprogram code into a deployable package (`project.build`).
        *   Upload the package to the configured FinClip server and App ID (`project.upload`).
7.  **`package.json` Scripts:** Provides convenient `npm run` commands (`deploy:dev`, `deploy:prod`) to orchestrate the secrets injection and build/upload process.

## Prerequisites

*   **AWS Credentials:** Your local machine or CI environment must have valid AWS credentials configured with permissions to read the specific secret from AWS Secrets Manager. Common methods include:
    *   AWS credentials file (`~/.aws/credentials`).
    *   AWS environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`).
    *   IAM role attached to an EC2 instance or ECS task (for CI/CD environments).
*   **FinClip App IDs:** You need the correct FinClip App IDs for your development and production environments. These must be configured in `upload.json`.
*   **Node.js & npm:** Required to run the scripts.
*   **Dependencies Installed:** Run `npm install` before attempting deployment.

## Configuration Files

*   **`upload.json`:**
    *   Update the `appId` fields under `development` and `prod` with your actual FinClip App IDs.
    *   Before deploying a new version, **manually update the `version` field** for the target environment (e.g., increment from "0.0.1" to "0.0.2"). The `desc` field is optional but recommended for describing the build.
    ```json
    {
      "development": {
        "desc": "Boilerplate Development Build v0.0.2", // Update desc
        "path": "./",
        "appId": "your-dev-finclip-appid", // Replace placeholder
        "version": "0.0.2" // Manually update version
      },
      "prod": {
          "desc": "Boilerplate Production Build v1.0.0", // Update desc
          "path": "./",
          "appId": "your-prod-finclip-appid", // Replace placeholder
          "version": "1.0.0" // Manually update version
      }
    }
    ```

*   **`inject-secrets-*.js`:**
    *   Verify the `region` and `secret_name` variables within these files point to the correct AWS Secrets Manager location for your organization. Modify if necessary.

## Deployment Steps

1.  **Ensure Prerequisites:** Verify AWS credentials, Node.js/npm, and run `npm install`.
2.  **Update Version:** Manually update the `version` (and optionally `desc`) in `upload.json` for the environment you are deploying to.
3.  **Commit Changes:** Commit your code changes and the updated `upload.json` to Git.
4.  **Run Deployment Script:**
    *   **For Development:**
        ```bash
        npm run deploy:dev
        ```
    *   **For Production:**
        ```bash
        npm run deploy:prod
        ```

**What the script does:**

*   `npm run secrets:dev` (or `prod`) executes the corresponding `inject-secrets-*.js` script.
    *   Connects to AWS Secrets Manager.
    *   Fetches `MPOpenAPISecret` and `MPServerUrl`.
    *   Creates/overwrites the `.env` file with these secrets and `NODE_ENV=development` (or `prod`).
*   `node build.js` executes the main build script.
    *   Loads environment variables from `.env` using `dotenv`.
    *   Reads `appId` and `version` from `upload.json` based on `NODE_ENV`.
    *   Validates configuration.
    *   Runs FinClip's `packNpm` and `project.build`.
    *   Runs FinClip's `project.upload`, sending the built package to the specified `MPServerUrl` for the given `appId` and `version`, using the `MPOpenAPISecret` for authentication.

5.  **Verify Deployment:** Check the FinClip Management Portal for the newly uploaded version of your miniprogram under the corresponding App ID. You can then proceed with testing or releasing it through the portal.

## CI/CD Integration

This setup is designed to be integrated into a CI/CD pipeline with Jenkins.

*   **Secrets:** The CI/CD environment needs secure access to AWS credentials (e.g., via IAM roles or securely injected environment variables). It will run the `inject-secrets` script just like a local deployment.
*   **Environment:** The CI/CD pipeline must set the `NODE_ENV` variable correctly (`development` or `prod`) before running the `npm run deploy:*` command to ensure the correct configuration is used.

## Troubleshooting

*   **AWS Credentials Error:** Ensure your AWS credentials are correctly configured and have permission to access the specified secret in Secrets Manager. Check the region in `inject-secrets-*.js`.
*   **FinClip Upload Error:**
    *   Verify `MPOpenAPISecret` and `MPServerUrl` in AWS Secrets Manager are correct.
    *   Check if the `appId` in `upload.json` is correct for the target environment.
    *   Ensure the FinClip server is reachable from your machine or CI environment.
    *   Check the console output from `build.js` for specific error messages from `@finclip/applet-builder-ci`.
*   **Dependency Errors:** Ensure `npm install` was run successfully. Check `.npmrc` configuration if private packages fail to install.
*   **Build Errors:** Check console output for errors during the `packNpm` or `project.build` phases. These could be related to code syntax errors or issues with the FinClip build tools.
