# Internal Gateway Routing Rules

## Add a new service

To add a  new service to the Internal Gateway you need to create a configuration file following these instructions:

1. Create a branch from the branch that you want to target -- e.g. if you want to make changes in **main**, create a
   branch from **main** and the PR against **main**. Do this for every environment that needs the change.

2. Must be created under `/resources/<lane>/<service-name>.json` using the `service-template.json` file as base:
   - The file should be under the directory of the Lane who owns the service.
   - The filename should match the service repository name.

3. It must follow this [structure](https://powerupai.atlassian.net/wiki/spaces/PLATFORM/pages/3390767109/User+Guide).

4. Create a PR including the link to the repository of the new service and the related Jira ticket(s).

5. Once the PR is approved, the changes should take effect a few minutes later.
