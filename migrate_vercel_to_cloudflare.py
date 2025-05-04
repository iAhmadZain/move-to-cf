#!/usr/bin/env python3

import requests
import json
import argparse
import os

# Vercel API base URL
VERCEL_API_BASE = "https://api.vercel.com"

# Cloudflare API base URL
CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"

def get_vercel_projects(api_token):
    """Fetches the list of projects from Vercel."""
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    url = f"{VERCEL_API_BASE}/v9/projects"
    projects = []
    while url:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            projects.extend(data.get('projects', []))
            # Handle pagination
            pagination = data.get('pagination', {})
            next_page = pagination.get('next')
            if next_page:
                url = f"{VERCEL_API_BASE}/v9/projects?until={next_page}"
            else:
                url = None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Vercel projects: {e}")
            if response is not None:
                print(f"Response status: {response.status_code}")
                print(f"Response text: {response.text}")
            return None
    return projects

def get_vercel_project_details(api_token, project_id):
    """Fetches detailed information for a specific Vercel project."""
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    details = {}

    # Get basic project info (includes build settings)
    try:
        url_project = f"{VERCEL_API_BASE}/v9/projects/{project_id}"
        response = requests.get(url_project, headers=headers)
        response.raise_for_status()
        details['info'] = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Vercel project info for {project_id}: {e}")
        return None

    # Get environment variables
    try:
        url_env = f"{VERCEL_API_BASE}/v9/projects/{project_id}/env"
        response = requests.get(url_env, headers=headers)
        response.raise_for_status()
        details['env_vars'] = response.json().get('envs', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Vercel env vars for {project_id}: {e}")
        # Continue even if env vars fail, maybe project has none
        details['env_vars'] = []

    # Get domains
    try:
        url_domains = f"{VERCEL_API_BASE}/v9/projects/{project_id}/domains"
        response = requests.get(url_domains, headers=headers)
        response.raise_for_status()
        details['domains'] = response.json().get('domains', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Vercel domains for {project_id}: {e}")
        # Continue even if domains fail
        details['domains'] = []

    return details

def create_cloudflare_pages_project(cf_api_token, cf_account_id, vercel_project_details):
    """Creates a Cloudflare Pages project based on Vercel project details."""
    headers = {
        "Authorization": f"Bearer {cf_api_token}",
        "Content-Type": "application/json"
    }
    url = f"{CLOUDFLARE_API_BASE}/accounts/{cf_account_id}/pages/projects"

    vercel_info = vercel_project_details.get('info', {})
    vercel_env_vars = vercel_project_details.get('env_vars', [])
    # Vercel domains are not directly transferable in the same way via API during creation
    # Custom domains need to be added to Cloudflare Pages project *after* creation.

    project_name = vercel_info.get('name')
    if not project_name:
        print("Skipping project: Missing name in Vercel details.")
        return None

    # --- Map Vercel settings to Cloudflare Pages --- 
    # This mapping is complex and depends heavily on the Vercel project type.
    # Cloudflare Pages primarily works with Git repos or direct uploads.
    # This script currently assumes a Git-connected project on Vercel.
    
    repo_info = vercel_info.get('link')
    build_settings = vercel_info.get('build', {})
    framework = vercel_info.get('framework')
    
    # Basic build config mapping (Needs refinement based on actual Vercel project types)
    build_config = {
        "build_command": vercel_info.get('buildCommand'),
        "output_dir": vercel_info.get('outputDirectory'),
        "root_dir": vercel_info.get('rootDirectory') or "/", # Default root
        "web_analytics_tag": None, # Optional
        "web_analytics_token": None # Optional
    }

    # Environment variables mapping (handle sensitive values appropriately)
    # Note: Cloudflare Pages has 'preview' and 'production' environments.
    # Vercel has 'production', 'preview', 'development'. We map Vercel's production/preview.
    environment_variables = {}
    preview_environment_variables = {}
    for var in vercel_env_vars:
        # Simple mapping: put all vars in production, duplicate for preview if applicable
        # Vercel API v9 env endpoint returns 'target' as array: ['production', 'preview', 'development']
        targets = var.get('target', [])
        var_name = var.get('key')
        var_value = var.get('value') # WARNING: This fetches the actual value. Handle securely.
        var_type = var.get('type') # 'secret', 'encrypted', 'plain'
        
        if var_name and var_value:
            # Cloudflare expects simple key-value pairs for non-secret vars.
            # Secrets need different handling (not fully supported via basic create API? Check CF docs)
            # For now, treat all as plain text for simplicity in this example.
            # TODO: Implement proper secret handling if CF API supports it during creation.
            if 'production' in targets:
                environment_variables[var_name] = var_value
            if 'preview' in targets:
                 preview_environment_variables[var_name] = var_value

    # --- Prepare Cloudflare API Payload --- 
    # This needs to be adjusted based on whether it's a Git project or direct upload.
    # Assuming Git for now.
    if not repo_info or repo_info.get('type') != 'github': # Assuming GitHub for now
        print(f"Skipping project '{project_name}': Not linked to a GitHub repository or link info missing.")
        print("Cloudflare Pages API project creation primarily supports Git repos or direct uploads.")
        print("Manual migration or direct upload might be needed for non-Git projects.")
        return None

    payload = {
        "name": project_name,
        "production_branch": vercel_info.get('productionBranch') or 'main', # Default to main
        "build_config": build_config,
        "source": {
            "type": "github",
            "config": {
                "owner": repo_info.get('org'),
                "repo_name": repo_info.get('repo'),
                "production_branch": vercel_info.get('productionBranch') or 'main',
                "pr_comments_enabled": True, # Default
                "deployments_enabled": True # Default
            }
        },
        "deployment_configs": {
            "preview": {
                "environment_variables": preview_environment_variables
            },
            "production": {
                "environment_variables": environment_variables
            }
        }
    }

    # --- Make the API Call --- 
    try:
        print(f"Attempting to create Cloudflare Pages project for: {project_name}")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        print(f"Successfully created Cloudflare Pages project: {result.get('result', {}).get('name')}")
        print(f"Subdomain: {result.get('result', {}).get('subdomain')}")
        # TODO: Add logic to configure custom domains using CF API after project creation.
        return result.get('result')
    except requests.exceptions.RequestException as e:
        print(f"Error creating Cloudflare Pages project for {project_name}: {e}")
        if response is not None:
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Migrate projects from Vercel to Cloudflare Pages.')
    parser.add_argument('--vercel-token', required=True, help='Vercel API Token')
    parser.add_argument('--cf-token', required=True, help='Cloudflare API Token')
    parser.add_argument('--cf-account-id', required=True, help='Cloudflare Account ID')
    parser.add_argument('--project-id', help='Specific Vercel project ID to migrate (optional)')

    args = parser.parse_args()

    print("Fetching Vercel projects...")
    if args.project_id:
        print(f"Fetching details for specific project ID: {args.project_id}")
        project_details = get_vercel_project_details(args.vercel_token, args.project_id)
        if project_details:
            create_cloudflare_pages_project(args.cf_token, args.cf_account_id, project_details)
        else:
            print(f"Could not fetch details for project {args.project_id}")
    else:
        vercel_projects = get_vercel_projects(args.vercel_token)
        if not vercel_projects:
            print("Failed to fetch Vercel projects or no projects found.")
            return

        print(f"Found {len(vercel_projects)} Vercel projects. Processing...")
        for project in vercel_projects:
            project_id = project.get('id')
            project_name = project.get('name')
            print(f"\n--- Processing Vercel Project: {project_name} (ID: {project_id}) ---")
            if not project_id:
                print("Skipping project: Missing ID.")
                continue
            
            project_details = get_vercel_project_details(args.vercel_token, project_id)
            if project_details:
                # Check if project is suitable for automatic migration (e.g., GitHub linked)
                if project_details.get('info', {}).get('link', {}).get('type') == 'github':
                     create_cloudflare_pages_project(args.cf_token, args.cf_account_id, project_details)
                else:
                    print(f"Skipping automatic migration for '{project_name}': Project is not linked via GitHub or link type is unsupported.")
                    print("Manual migration or direct upload to Cloudflare Pages might be required.")
            else:
                print(f"Skipping project {project_name}: Failed to fetch details.")

    print("\nMigration process finished.")

if __name__ == "__main__":
    main()


