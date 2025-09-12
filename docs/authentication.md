# Authentication System

This system supports multiple authentication methods configurable via environment variables (`.env`).  
It can operate in **internal-only**, **partner-only**, or **hybrid** mode.  
Additionally, **Superadmin authentication** is always enabled and bypasses standard authentication checks.  

---

## 1. Authentication Modes

Authentication mode is set in the `.env` file:

```env
AUTH_MODE=both   # Options: internal | partner | both
```

**Modes:**
- **`internal`** → Only API Key authentication is enabled.  
- **`partner`** → Only OAuth2 (JWT) authentication is enabled.  
- **`both`** → Both methods are accepted. OAuth2 is attempted first; if it fails, API Key authentication is checked.  

---

## 2. Superadmin Authentication

Superadmin provides **unrestricted privileged access** to all endpoints.  
This authentication is always active, regardless of the `AUTH_MODE` setting.  

- Requests must include the query parameter **`superAdminKey`**.  
- This key must match the configured value in `.env`:  

```env
SUPER_ADMIN_API_KEY=your-superadmin-secret
```

On application startup:
- A Superadmin **tenant** and **client** are automatically created in the database.  
- This account bypasses all standard restrictions and policies.  

---

## 3. API Key Authentication (Internal Mode)

Designed for **internal and trusted systems**.  

### Request Format
Clients authenticate using an API key passed in the request headers:

```
X-API-Key: <your-secret-api-key>
```

---

## 4. OAuth2 / JWT Authentication (Partner Mode)

Used for **external or partner integrations**.  

### Request Format
Clients authenticate by passing a JWT token in the request header:

```
Authorization: Bearer <jwt-token>
```

### JWT Details
- **Algorithm:** RS256  
- **Signing keys:** Retrieved from the tenant’s JWKS (JSON Web Key Set).  
- **Expiration:** Configurable via `.env`:  

```env
ACCESS_TOKEN_EXPIRE_MINUTES=60   # Default expiry time in minutes
```

Example:
```env
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 5. Mode Comparison

| Mode     | Method                      | Header Example                              |
| -------- | --------------------------- | ------------------------------------------- |
| Internal | API Key                     | `X-API-Key: mySecretInternalKey123`         |
| Partner  | OAuth2 (JWT)                | `Authorization: Bearer eyJhbGciOi...`       |
| Both     | OAuth2, fallback to API Key | OAuth2 validated first, API Key if it fails |

---

## 6. Account Model and Access Control

The authentication system is structured around three entity levels:

- **Tenant** → Represents an organization, owning multiple clients.  
- **Client** → Represents an application within a tenant. Issues API keys.  
- **API Key** → Represents credentials tied to a client.  

---

### Tenant State Management
- **Initial State:**  
  When a tenant is created, it is provisioned in an **inactive** state by default.  
  - Inactive tenants **cannot authenticate** requests.  
  - All Clients and API Keys under an inactive tenant are also considered effectively disabled until activation.  

- **Activation:**  
  Only a **Super Admin** has the authority to activate or deactivate a tenant.  
  - Once activated, the tenant and its dependent Clients and API Keys are eligible to operate subject to their policies.  
  - A deactivated tenant will immediately suspend access for all dependent resources.  

- **Operational Impact:**  
  - **Inactive Tenant:** Rejects all requests with an authentication error (e.g., `403 Forbidden - Tenant Inactive`).  
  - **Active Tenant:** Policies (IP, scope, rate limits) are evaluated as described below.  

---

### Policies
Access policies control authentication across **Tenant**, **Client**, and **API Key** levels. All levels support:  

1. **IP Restrictions**  
   Restrict calls by IP. Supported formats:  
   - Exact IP: `192.168.0.10`  
   - CIDR: `192.168.0.0/24`  
   - Wildcard: `10.0.*.*`  
   - Range: `192.168.0.50-192.168.0.100`  
   - Any (`*`) → Not recommended in production.  

2. **Scope Restrictions (Required for Endpoint Access)**  
   Each API endpoint requires specific scopes. A token or API key **must include the matching scope** to access the endpoint. For example:  
   - `all` → Full system-wide access  
   - `tenant` → Tenant-level operations  
   - `qdrant` → Vector database APIs  
   - `meal_plan` → Meal plan-related APIs  
   - `generate` → Meal plan generation services  
   - `validate` → Meal plan validation APIs  
   - `version_service` → Version management endpoints  

   **Important:** Authentication alone is not sufficient; the credential must also carry the **required scope** for the requested endpoint.  

3. **Rate Limits**  
   Restrict the number of requests allowed in a given timeframe per credential.  

---

### Policy Precedence
Policies are hierarchical and cumulative:  

- **API Key access** → Policies of API Key, Client, and Tenant all apply.  
- **Client access** → Controlled by Client and Tenant policies.  
- **Tenant access** → Global restrictions apply across all Clients and API Keys.  

---

### State + Policy Enforcement
1. **Check Tenant State:** If tenant is inactive → deny request.  
2. **Apply Hierarchical Policies:** If tenant is active → evaluate restrictions from Tenant, Client, and API Key.  
3. **Verify Required Scope:** Explicit matching scope must be present.  
4. **Enforce Rate Limits.**  
---

## 7. Summary

- Authentication can be configured as **internal**, **partner**, or **both**.  
- **Superadmin authentication** (via `SUPER_ADMIN_API_KEY`) bypasses all restrictions.  
- **Internal systems** use API Key authentication.  
- **Partner systems** use OAuth2 JWT-based authentication.  
- **All account models (Tenant, Client, API Key)** support policies for IP restrictions, scope restrictions, and rate limiting.  
- **Scopes are required to access endpoints** — credentials without the correct scope will be denied, even if authentication succeeds.  
- Policies cascade hierarchically: **Tenant → Client → API Key**.  