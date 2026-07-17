# Agentic Workflow Diagrams

These diagrams describe how the workspace guides a local coding agent without
forcing the whole repository corpus into the prompt.

## Context Routing

```mermaid
flowchart TD
  A["User asks for Jira/service change"] --> B["Agent reads contexts/current/service-context.yml"]
  B --> C{"repository_topology"}
  C -->|same-repo| D["Open service repo paths"]
  C -->|split-qa| E["Open service repo + qa-steps + qa-projects"]
  C -->|separate deployment| F["Open deployment repo or deployment folder"]
  D --> G["Inspect endpoint, DTO, contract, tests"]
  E --> G
  F --> H["Check ports, probes, env vars, image/runtime assumptions"]
  G --> I["Apply smallest code, contract, and test change"]
  H --> I
  I --> J["Run verification commands from YAML"]
  J --> K["Report changed files and validation result"]
```

## Same-Repo Topology

```mermaid
flowchart LR
  A["service-context.yml"] --> B["service repo"]
  B --> C["src/main/java endpoint + service"]
  B --> D["OpenAPI contract"]
  B --> E["src/test/java unit/integration/API tests"]
  B --> F["k8s/deployments folder"]
  C --> G["Behavior change"]
  D --> G
  E --> G
  F --> G
```

Use this when the team owns endpoint code, contract, tests, and deployment
assets in one repository.

## Split-QA / GitOps Topology

```mermaid
flowchart LR
  A["service-context.yml"] --> B["service repo"]
  A --> C["qa-steps"]
  A --> D["qa-projects/<service>-api-tests"]
  A --> E["deployment repo"]
  B --> F["Endpoint, DTO, OpenAPI"]
  C --> G["Reusable RestAssured utilities"]
  D --> H["Service-specific API tests"]
  E --> I["Kubernetes/GitOps assets"]
  F --> J["Validated service change"]
  G --> J
  H --> J
  I --> J
```

Use this when shared QA utilities or deployment manifests are maintained outside
the service repository.

## Context Efficiency Loop

```mermaid
sequenceDiagram
  participant User
  participant Agent
  participant YAML as service-context.yml
  participant Skill as SKILL.md
  participant Repo as Local repos
  participant Tests as Verification

  User->>Agent: Request service change
  Agent->>Skill: Load stable workflow rules
  Agent->>YAML: Read dynamic ticket context
  YAML-->>Agent: Endpoint, fields, topology, repo paths
  Agent->>Repo: Read only relevant files
  Agent->>Repo: Edit code, contract, tests, deployment if needed
  Agent->>Tests: Run required commands
  Tests-->>Agent: Pass/fail result
  Agent-->>User: Summary with changed files and validation
```

The efficiency claim is simple: keep the YAML and skills small, then let the
agent open files only after the task context points to them.

