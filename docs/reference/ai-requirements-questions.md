# AI Code Generation Requirements Questions

When prompting AI to generate code for enterprise features like the NEX epics (risk management, identity security, MSP experiences), use these questions to ensure comprehensive implementation. These questions help uncover functional, non-functional, and architectural considerations that AI might miss without explicit prompting.

## Functional Requirements

### Core Functionality
- What are the exact acceptance criteria for this feature?
- What edge cases must be handled (empty states, null values, missing data)?
- What validations are required (input validation, business rules, data constraints)?
- What are the success and error states for each operation?
- What happens when data is partial or incomplete?
- Are there any specific data transformations required?
- What default values should be used when data is missing?

### User Experience
- What loading states are needed (spinners, skeletons, progress indicators)?
- How should errors be displayed to users (toasts, inline, modals)?
- What accessibility requirements must be met (ARIA labels, keyboard navigation, screen readers)?
- Are there performance expectations (page load time, render time, query response time)?
- What responsive design considerations apply (mobile, tablet, desktop)?
- Should actions be optimistic or wait for confirmation?
- What confirmation dialogs are needed for destructive actions?

### Data Flow
- Where does the data originate (GraphQL, REST, Kafka, cache)?
- What data needs to be cached and for how long?
- How should stale data be handled?
- What happens when real-time updates occur while user is viewing data?
- Are there data consistency requirements across services?
- What is the data retention policy?

## Non-Functional Requirements

### Performance
- What are the expected data volumes (10 records, 1000, 10000+)?
- Are there pagination requirements (offset-based, cursor-based)?
- What are the query performance targets (p50, p95, p99)?
- Should queries use indexes? Which columns?
- Are there any caching strategies to implement?
- What is the expected concurrent user load?
- Are there rate limiting considerations?

### Scalability
- How will this feature scale as data grows?
- Are there batch processing requirements?
- Should operations be async or sync?
- What happens if a query times out?
- Are there memory constraints to consider?
- Should we implement pagination for all list operations?

### Security
- What authentication is required?
- What authorization/permission checks are needed?
- Are there tenant isolation requirements (MSP multi-tenant)?
- What data should be logged (avoiding PII)?
- Are there data sanitization requirements (XSS, SQL injection)?
- What secrets or credentials need secure storage?
- Are there compliance requirements (GDPR, SOC2, CISA)?

### Observability
- What should be logged (info, warn, error levels)?
- What metrics should be tracked (counters, gauges, histograms)?
- What tracing/telemetry is needed?
- How will we debug issues in production?
- What alerts should be configured?
- Are there audit trail requirements?

### Reliability
- What is the error handling strategy?
- How should retries be implemented (exponential backoff)?
- What is the fallback behavior when services are down?
- Are there circuit breaker patterns to implement?
- What is the disaster recovery plan?
- How should data migrations be rolled back?

## Architecture & Integration

### Backend
- Which service owns this feature (entraid-service, alerting-service)?
- What database entities need to be created or modified?
- Are database migrations required? (Entity Framework migrations)
- What GraphQL schema changes are needed?
- Are new API endpoints required (REST, GraphQL, gRPC)?
- What DTOs/models need to be created or updated?
- How does this integrate with existing services?
- What Kafka topics/events are involved?
- Are there schema registry validations required (nexus-schemas)?

### Frontend
- Which repository handles the UI (nexus-ui-host)?
- What React components need to be created or modified?
- Are there Barracuda Design System (BDS) components to use?
- What state management is needed (React Query, Context, Zustand)?
- What GraphQL queries/mutations are required?
- How should GraphQL Mesh be configured?
- Are there routing/navigation changes?
- What browser compatibility is required?

### Data Schema
- Does the schema match existing patterns in the codebase?
- Are schema changes backward compatible?
- How will schema validation work (Kafka Schema Registry)?
- Are there versioning considerations for schemas?
- What happens to existing data when schema changes?

### Cross-Service Concerns
- How do services communicate (sync vs async)?
- What happens if a dependent service is unavailable?
- Are there transaction boundaries across services?
- How is eventual consistency handled?
- What is the retry policy for failed messages?
- How are duplicate messages handled (idempotency)?

## Testing

### Test Coverage
- What unit tests are required?
- What integration tests are needed?
- Are end-to-end tests necessary?
- How will we test error scenarios?
- What mocking strategy should be used?
- Are there performance tests required?
- How will we test multi-tenant scenarios (MSP)?

### Test Data
- What test data is needed?
- How will test data be seeded?
- Are there data cleanup requirements?
- How do we test with realistic data volumes?

## Deployment & Operations

### Deployment
- What is the deployment strategy (blue-green, canary, rolling)?
- Are there feature flags needed?
- What is the rollback plan?
- Are there database migration scripts?
- What configuration changes are required?
- Are there environment-specific settings?

### Monitoring
- What dashboards need to be created?
- What are the SLOs/SLAs for this feature?
- What alerts should trigger on-call?
- How will we measure success metrics?

### Documentation
- What API documentation is needed?
- Are there user-facing docs to update?
- What inline code comments are required?
- Are there architecture diagrams to create/update?
- What runbooks are needed for operations?

## Domain-Specific Questions

### For Risk/Security Features (NEX-6260, NEX-6187, NEX-6268)
- What is the risk detection logic?
- How are risks classified and prioritized?
- What remediation guidance should be provided?
- How are risks resolved (manual, automatic)?
- What evidence needs to be collected and displayed?
- How are historical risks tracked?
- Are there compliance requirements (CISA baselines)?
- What is the false positive rate tolerance?

### For MSP/Multi-Tenant Features (NEX-6204)
- How is tenant isolation enforced?
- How do MSPs switch between customer contexts?
- What data is aggregated across tenants vs. per-tenant?
- Are there different permission models for MSPs vs. direct customers?
- How are customer account IDs/identifiers managed?
- What happens when a customer is removed from MSP management?

### For UI/Dashboard Features (NEX-6200)
- What are the visual design specs (Figma, prototype)?
- Are there design system components to use or extend?
- What are the information hierarchy and visual priority?
- How should trend indicators be calculated and displayed?
- What color schemes/themes are supported (light/dark mode)?
- Are there animation or transition requirements?
- What empty states and zero-data scenarios exist?

### For Pagination/Export Features (NEX-6260)
- What pagination strategy (offset, cursor, seek)?
- What page sizes are supported?
- How are total counts calculated (exact vs. estimate)?
- What export formats are supported (CSV, JSON, Excel)?
- What is the maximum export size?
- Should exports be synchronous or asynchronous?
- How are large exports streamed or chunked?
- What CSV headers and column mappings are used?

### For Search/Filter Features
- What fields are searchable?
- What search algorithm (exact, fuzzy, full-text)?
- Are there search operators (AND, OR, NOT)?
- What filters are available (dropdowns, multi-select)?
- How are filters combined (AND vs. OR)?
- Are saved searches/filters needed?
- What is the search latency requirement?

## Common Pitfalls to Avoid

### Code Quality
- Am I following existing code patterns in the repository?
- Am I avoiding code duplication?
- Are variable/function names clear and consistent?
- Am I handling null/undefined properly?
- Am I using appropriate error types?
- Are there magic numbers/strings that should be constants?

### Performance Anti-Patterns
- Am I making N+1 queries?
- Am I loading more data than needed?
- Am I computing expensive operations in render loops?
- Am I missing opportunities to parallelize operations?
- Am I caching data that should be fresh?

### Security Anti-Patterns
- Am I exposing sensitive data in logs or errors?
- Am I properly sanitizing user input?
- Am I checking permissions before operations?
- Am I using parameterized queries (avoiding SQL injection)?
- Am I storing secrets in code or config files?

### Integration Anti-Patterns
- Am I making synchronous calls where async would be better?
- Am I missing error handling for external services?
- Am I tightly coupling services unnecessarily?
- Am I forgetting to version APIs/schemas?

## Validation Checklist

Before submitting AI-generated code, verify:

- [ ] All acceptance criteria are met
- [ ] Error handling is comprehensive
- [ ] Loading states are implemented
- [ ] Empty states are handled
- [ ] Accessibility standards are met
- [ ] Performance requirements are satisfied
- [ ] Security checks are in place
- [ ] Tests are written and passing
- [ ] Code follows repository patterns
- [ ] Documentation is updated
- [ ] No hardcoded values that should be configurable
- [ ] No TODO comments without JIRA tickets
- [ ] Database indexes are created where needed
- [ ] GraphQL schema is validated
- [ ] Kafka schema is registered and validated
- [ ] Multi-tenant isolation is enforced (if applicable)
- [ ] Feature flags are implemented (if needed)
- [ ] Monitoring/logging is in place
- [ ] Backward compatibility is maintained
- [ ] Migration path exists for existing data

## Usage Examples

### Example 1: Prompting for Pagination Implementation
```
I need to implement server-side pagination for risk evidence. Consider:
- What pagination parameters should the GraphQL query accept (skip, take, cursor)?
- How should total counts be calculated without impacting performance?
- What happens when the underlying data changes while user is paginating?
- Should we use offset-based or cursor-based pagination for 1000+ records?
- How do we handle edge cases like negative offsets or invalid cursors?
- What indexes are needed for performant queries?
- How should the frontend maintain pagination state?
- What loading states should be shown during page transitions?
```

### Example 2: Prompting for MSP Cross-Tenant View
```
I need to display risks across all MSP customer tenants. Consider:
- How do we enforce tenant isolation while aggregating data?
- What performance impact does querying 100+ customer tenants have?
- Should we implement pagination for the customer list?
- How do users navigate between customer contexts without losing state?
- What caching strategy should we use for cross-tenant data?
- How do we handle customers with no risks vs. customers with 1000+ risks?
- What happens when an MSP loses access to a customer mid-session?
- How are tenant IDs validated and sanitized?
```

### Example 3: Prompting for CSV Export
```
I need to implement CSV export for risk evidence. Consider:
- What is the maximum number of records we should export?
- Should the export be synchronous or asynchronous for large datasets?
- How do we handle special characters in CSV fields (quotes, commas, newlines)?
- What CSV encoding should we use (UTF-8, UTF-8 BOM)?
- Should we stream the CSV or build it in memory?
- How do we handle fields with null values in the CSV?
- What HTTP headers are needed for browser download?
- Should exports respect the current filter/search state?
- What error messages should be shown if export fails?
- Do we need to rate-limit export requests?
```

## When to Ask "What Else Should We Consider?"

Ask this question when:
- The requirements are high-level without implementation details
- You're implementing a feature similar to existing ones
- Security or compliance is involved
- The feature involves multiple services or repositories
- Performance at scale is critical
- The user experience has many edge cases
- You're modifying shared schemas or contracts
- The feature has cross-tenant or MSP implications
- There are deployment or migration complexities
- You need to maintain backward compatibility
