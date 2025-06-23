# Hyperlane Authorization

This repo contains authorization rules to manage Hyperlane APIs. It controls which clients have
access to each service on Hyperlane.

## Glossary

**Service**: A service is an HTTP endpoint belonging to an API on hyperlane. An example of a service
if `GET /users/{user_id}`.

**Application**: An application represents the entities that expose or consume services. An application
can own services that it exposes to other applications and it can also call services that other
applications own. Some examples of applications are `cards-api` and `stori-mobile-app`.

**Subscription**: In order for an application to consume other services, it must subscribe to the
service. This allows the owners of each service to know which applications are using it's service
without needing to dig through the logs or Grafana.

**Role**: Roles are the permission model for granting access for an application to access services.
A role can grant access to multiple services. For example, a `ReadUsers` role might grant
access to the `getUser`, `getUserAddress` and `getUserPhone` services.
