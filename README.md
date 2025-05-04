# Vercel to Cloudflare Pages Migration Script

This Python script assists in migrating projects hosted on Vercel to Cloudflare Pages. It automates fetching project configurations from Vercel and creating corresponding projects on Cloudflare Pages.

## Prerequisites

Before running the script, you need the following:

1.  **Python 3:** Ensure you have Python 3 installed on your system.
2.  **Requests Library:** Install the required Python library:
    ```bash
    pip install requests
    ```
3.  **Vercel API Token:**
    *   Go to your Vercel account settings.
    *   Navigate to the "Tokens" section.
    *   Create a new API token with appropriate permissions (read access to projects, environment variables, domains).
    *   Copy the generated token securely.
4.  **Cloudflare API Token:**
    *   Log in to your Cloudflare dashboard.
    *   Go to "My Profile" > "API Tokens".
    *   Create a custom token.
    *   Grant the token permissions for:
        *   Account Settings: Read
        *   Cloudflare Pages: Edit (or specific permissions needed for project creation/management)
        *   User Details: Read (needed to verify token)
    *   Configure the token to apply to your specific account resources.
    *   Copy the generated token securely.
5.  **Cloudflare Account ID:**
    *   Find your Account ID on the right sidebar of your Cloudflare dashboard's overview page for any domain, or in the URL when viewing account settings.

## Script Usage

Run the script from your terminal using the following command structure:

```bash
python migrate_vercel_to_cloudflare.py --vercel-token YOUR_VERCEL_API_TOKEN --cf-token YOUR_CLOUDFLARE_API_TOKEN --cf-account-id YOUR_CLOUDFLARE_ACCOUNT_ID [--project-id OPTIONAL_VERCEL_PROJECT_ID]
```

**Arguments:**

*   `--vercel-token`: (Required) Your Vercel API token.
*   `--cf-token`: (Required) Your Cloudflare API token.
*   `--cf-account-id`: (Required) Your Cloudflare Account ID.
*   `--project-id`: (Optional) If you want to migrate only a specific Vercel project, provide its ID here. If omitted, the script will attempt to migrate all accessible projects.

## Functionality

1.  **Connects to Vercel:** Uses the provided Vercel token to authenticate.
2.  **Fetches Projects:** Retrieves a list of all your Vercel projects or the specific project if an ID is provided.
3.  **Gathers Details:** For each project, it fetches:
    *   Basic project information (name, framework, linked repository, production branch).
    *   Build settings (build command, output directory, root directory).
    *   Environment variables (both production and preview).
    *   Associated domains (though these are not automatically configured on Cloudflare).
4.  **Connects to Cloudflare:** Uses the provided Cloudflare token and account ID.
5.  **Creates Cloudflare Pages Project:** Attempts to create a new Cloudflare Pages project corresponding to the Vercel project. It maps the build settings and environment variables.

## Assumptions and Limitations

*   **GitHub-Linked Projects:** The script is primarily designed for Vercel projects linked to GitHub repositories. Cloudflare Pages project creation via API heavily relies on Git integration. Projects deployed through other means (like Vercel CLI direct deploys without Git linking) will likely be skipped, and a message will be printed.
*   **Environment Variable Handling:** The script fetches environment variable values. Cloudflare Pages has specific mechanisms for handling secrets, which might differ from Vercel. This script currently maps variables as plain text during creation. You may need to manually configure secrets in the Cloudflare dashboard or adjust the script if the Cloudflare API offers specific secret handling during project creation.
*   **Custom Domains:** Migrating custom domains is **not** automated by this script. After a project is created on Cloudflare Pages, you must manually configure your custom domains within the Cloudflare dashboard for that specific Pages project.
*   **Build Configuration Mapping:** The script performs a basic mapping of Vercel build settings (command, output directory, root directory) to Cloudflare Pages settings. Complex build configurations might require manual adjustments in the Cloudflare Pages project settings after creation.
*   **Framework Compatibility:** Ensure the frameworks used in your Vercel projects are compatible with Cloudflare Pages build environments.
*   **API Rate Limits:** Be mindful of potential API rate limits on both Vercel and Cloudflare, especially when migrating a large number of projects.
*   **Testing Required:** This script interacts directly with your Vercel and Cloudflare accounts. **Thorough testing in a non-critical environment or with a single, non-production project is highly recommended before running it on all your projects.** The script requires valid credentials and cannot be tested by the AI assistant.

## Error Handling

The script includes basic error handling for API requests. If errors occur during fetching Vercel details or creating Cloudflare projects, it will print error messages to the console, including status codes and response text where available, and attempt to continue with the next project (if migrating all).

