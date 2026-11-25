# OpenAPI 3.1 Contract Generation Guide

Guide and boilerplate for mapping domain vertical slice contracts (`contract.ts` or Pydantic) into machine-readable OpenAPI 3.1 specifications.

---

## 1. OpenAPI 3.1 Core Skeleton (`openapi.yaml`)

```yaml
openapi: 3.1.0
info:
  title: Apex Ledger API
  version: 1.0.0
  description: High-performance multi-tenant ledger and billing engine.
servers:
  - url: http://localhost:8000/api
    description: Local development environment
  - url: https://api.apexledger.com/v1
    description: Production environment

paths:
  /billing/invoices:
    post:
      summary: Create customer invoice
      operationId: createInvoice
      tags:
        - Billing
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateInvoiceInput'
      responses:
        '201':
          description: Invoice created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InvoiceRecord'
        '400':
          $ref: '#/components/responses/BadRequestError'
        '401':
          $ref: '#/components/responses/UnauthorizedError'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    CreateInvoiceInput:
      type: object
      required:
        - tenantId
        - amountCents
        - dueDate
      properties:
        tenantId:
          type: string
          format: uuid
        amountCents:
          type: integer
          minimum: 1
          example: 4999
        dueDate:
          type: string
          format: date-time
          example: '2026-11-01T00:00:00Z'

    InvoiceRecord:
      type: object
      required:
        - id
        - tenantId
        - amountCents
        - status
        - createdAt
      properties:
        id:
          type: string
          format: uuid
        tenantId:
          type: string
          format: uuid
        amountCents:
          type: integer
        status:
          type: string
          enum: [draft, pending, paid, void]
        createdAt:
          type: string
          format: date-time

  responses:
    BadRequestError:
      description: Malformed payload or validation error (RFC 7807 Problem Details)
      content:
        application/problem+json:
          schema:
            type: object
            required: [type, title, status]
            properties:
              type:
                type: string
                example: "https://example.com/probs/validation-error"
              title:
                type: string
                example: "Validation failed"
              status:
                type: integer
                example: 400
              detail:
                type: string
                example: "One or more fields failed validation."

    UnauthorizedError:
      description: Missing or expired authentication token (RFC 7807 Problem Details)
      content:
        application/problem+json:
          schema:
            type: object
            required: [type, title, status]
            properties:
              type:
                type: string
                example: "https://example.com/probs/unauthorized"
              title:
                type: string
                example: "Unauthorized"
              status:
                type: integer
                example: 401
              detail:
                type: string
                example: "Missing or expired bearer token."
```

### Contract-to-OpenAPI Mapping Patterns
- **Zod (`contract.ts`)**: Map `z.object(...)` → `type: object` (`required` for non-optional keys), `z.enum([...])` → `enum`, `z.string().uuid()` → `format: uuid`, `z.string().datetime()` → `format: date-time`.
- **Pydantic**: Export `model_json_schema()` or FastAPI's `app.openapi()` directly into `components.schemas`.

---

## 2. Embedding Interactive Docs (Scalar / Swagger)

In Next.js or Express, mount Scalar or Swagger UI pointing to `openapi.yaml`:

```html
<!-- Embedded Scalar Interactive API Reference -->
<!doctype html>
<html>
  <head>
    <title>API Reference</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <script
      id="api-reference"
      data-url="/openapi.yaml">
    </script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>
```
