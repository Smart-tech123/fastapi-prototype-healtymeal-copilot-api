# Endpoints Documentation

**Authentication Mechanisms:**  
- **OAuth2 Password Flow** (`/auth/client/login`)  
- **API Key** (via `X-API-Key` header or `superAdminKey` query param for admin-level access)

This API consists of three main groups of endpoints:  
1. **Authentication Endpoints** (manage tenants, clients, and API keys)  
2. **Service Endpoints** (functional API services such as LLM meal plan generation, validation, etc.)  
3. **CRUD Endpoints** (system-level administrative endpoints, superadmin only)

---

## 1. Authentication Endpoints
Authentication endpoints allow you to register and manage **Tenants (organizations)**, **Clients (applications within a tenant)**, and **API Keys**.  

These are typically the first endpoints you’ll interact with in order to create entities and obtain credentials.

---

### 1.1 Tenant Authentication Endpoints

**POST `/auth/tenant/register` – Register New Tenant**  
Registers a new tenant (organization).  
- **Authentication:** none  
- **Request Body:** `tenant_name`, `description`, `access_policy` (IP restrictions, scopes, rate limits)  
- **Response:** Newly created tenant object including `tenant_id` and `status`  

**PUT `/auth/tenant/update` – Update Tenant**  
Updates existing tenant information.  
- **Authentication:** OAuth2/API Key (scope: `tenant`)  
- **Request Body:** Fields such as `tenant_name`, `description`, `access_policy`  
- **Response:** Updated tenant info  

**GET `/auth/tenant/get` – Get Tenant Information**  
Retrieves tenant details by authenticated request.  
- **Authentication:** OAuth2/API Key (scope: `tenant`)  
- **Response:** Tenant metadata, status, and access policy  

**DELETE `/auth/tenant/revoke` – Revoke Tenant**  
Revokes (soft-deletes/disables) a tenant.  
- **Authentication:** OAuth2/API Key (scope: `tenant`)  
- **Response:** Empty  

**GET `/auth/tenant/rotate` – Rotate Tenant Key**  
Rotates the JWT signing key for tenant without downtime.  
- **Authentication:** OAuth2/API Key (scope: `tenant`)  
- **Response:** Empty  

---

### 1.2 Client Authentication Endpoints

**POST `/auth/client/register` – Register Client**  
Registers a new client under a tenant.  
- **Authentication:** none (must reference valid `tenant_id`).  
- **Request Body:** `client_name`, `description`, `tenant_id`, `access_policy`  
- **Response:** Client details with `client_id` and `client_secret_plain`  

**POST `/auth/client/login` – Login & Get Token**  
Obtains an OAuth2 access token (password flow).  
- **Authentication:** none (requires `client_id` & `client_secret`)  
- **Request Body:** `client_id`, `client_secret` (form-encoded)  
- **Response:** Bearer token (`access_token`)  

**PUT `/auth/client/update` – Update Client**  
Updates client metadata or policy.  
- **Authentication:** OAuth2/API Key  
- **Request Body:** `client_name`, `description`, `access_policy`  
- **Response:** Updated client info  

**GET `/auth/client/get` – Get Client Details**  
Retrieves client metadata under authentication.  
- **Authentication:** OAuth2/API Key  

**DELETE `/auth/client/revoke` – Revoke Client**  
Revokes a client.  
- **Authentication:** OAuth2/API Key  

**GET `/auth/client/rotate` – Rotate Client Secret**  
Rotates the client secret (new `client_secret_plain` returned).  
- **Authentication:** OAuth2/API Key  

---

### 1.3 API Key Endpoints

**POST `/auth/api_key/create` – Create API Key**  
Creates an API key for a client.  
- **Authentication:** OAuth2/API Key  
- **Request Body:** `key_name`, `description`, `access_policy`  
- **Response:** API key metadata and **plain `key_plain`** for initial usage  

**PUT `/auth/api_key/update` – Update API Key**  
Updates API key attributes and access policy.  
- **Authentication:** API Key only  
- **Request Body:** `key_name`, `description`, `access_policy`  
- **Response:** Updated API key metadata  

**GET `/auth/api_key/get` – Get API Key Info**  
Retrieves API key details.  
- **Authentication:** API Key only  

**DELETE `/auth/api_key/revoke` – Revoke API Key**  
Deletes or deactivates an API key.  
- **Authentication:** API Key only  

---

## 2. Service Endpoints
Service endpoints provide operational API functionality such as meal plan generation, validation, version-management, and vector database (Qdrant) interactions.

---

### 2.1 LLM Food Plan Generation
**POST `/llm/generate-meal-plan` – Generate Food Plan JSON**  
Generates a structured meal plan using an LLM, based on a provided prompt.  
- **Authentication:** OAuth2/API Key (scope: `generate`)  
- **Request Body:** `prompt`, `prompt_version` (optional)  
- **Response:** Structured `meal_plan` JSON and metadata (including validation results and raw LLM output)  

---

### 2.2 Food Plan Management
Endpoints for creating, retrieving, updating, and deleting meal plans.  
**Authentication:** OAuth2/API Key, scope `meal_plan`

- **GET `/meal-plan/`**: List all saved meal plans  
- **POST `/meal-plan/`**: Create a new meal plan (JSON schema enforcement)  
- **GET `/meal-plan/{id}`**: Retrieve meal plan by ID  
- **PUT `/meal-plan/{id}`**: Update an existing meal plan (with version logging)  
- **DELETE `/meal-plan/{id}`**: Delete a meal plan  

---

### 2.3 Food Plan Validation
**POST `/validate/validate-meal-plan` – Validate Food Plan JSON**  
Performs schema validation on a meal plan JSON definition. Returns errors with exact field locations.  
- **Authentication:** OAuth2/API Key, scope `validate`  
- **Request Body:** JSON object representing a meal plan definition  
- **Response:** `ValidationResult` (boolean valid, errors, parsed model)  

---

### 2.4 Version Management (Food Plan Version Control)
Tracks and manages version logs for meal plans. Supports rollback.  
**Authentication:** OAuth2/API Key, scope `version_service`

- **GET `/version-service/meal-plan/{meal_plan_id}`**: Get logs for a specific meal plan  
- **GET `/version-service/meal-plan/{meal_plan_id}/{log_id}`**: Get archived meal plan at that log version  
- **GET `/version-service/log/{log_id}`**: Get details of a single version log  
- **POST `/version-service/rollback/{meal_plan_id}/{log_id}`**: Rollback meal plan to a specific log  

---

### 2.5 Qdrant Vector Database Service
Provides direct access to the vector search database for storing/searching embeddings.  
**Restricted:** SuperAdmin / `qdrant` scope  

- **GET `/qdrant/{collection_name}`**: Get all points in collection  
- **POST `/qdrant/{collection_name}`**: Insert point (vector + payload)  
- **GET `/qdrant/{collection_name}/{point_id}`**: Retrieve point by ID  
- **PUT `/qdrant/{collection_name}/{point_id}`**: Update point (vector/payload)  
- **DELETE `/qdrant/{collection_name}/{point_id}`**: Delete point  
- **POST `/qdrant/{collection_name}/search`**: Vector similarity search  

---

## 3. CRUD Endpoints
Low-level **administrative data access endpoints**.  
**Restricted:** SuperAdmin only (authenticated via `superAdminKey`).  
They expose full CRUD operations for internal models:

### 3.1 Tenant CRUD
Endpoints for Tenant entity data.  
- `GET /crud/tenant/`, `POST /crud/tenant/`  
- `GET/PUT/DELETE /crud/tenant/{id}`  

### 3.2 Client CRUD
Endpoints for Clients.  
- `GET /crud/client/`, `POST /crud/client/`  
- `GET/PUT/DELETE /crud/client/{id}`  

### 3.3 API Key CRUD
Endpoints for API Key instances.  
- `GET /crud/api_key/`, `POST /crud/api_key/`  
- `GET/PUT/DELETE /crud/api_key/{id}`  

### 3.4 Food Plan CRUD
Raw Meal plan data management.  
- `GET /crud/meal-plan/`, `POST /crud/meal-plan/`  
- `GET/PUT/DELETE /crud/meal-plan/{id}`  

### 3.5 Version Log CRUD
Version log persistence.  
- `GET /crud/version-log/`, `POST /crud/version-log/`  
- `GET/PUT/DELETE /crud/version-log/{id}`  

### 3.6 Retry Metadata CRUD
Tracks retries for failed operations.  
- `GET /crud/retry-metadata/`, `POST /crud/retry-metadata/`  
- `GET/PUT/DELETE /crud/retry-metadata/{id}`  
- `POST /crud/retry-metadata/search` → advanced filtering  

### 3.7 Audit Log CRUD
Audit log tracking entity.  
- `GET /crud/audit-log/`, `POST /crud/audit-log/`  
- `GET/PUT/DELETE /crud/audit-log/{id}`  