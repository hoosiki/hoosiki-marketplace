# Vanilla JavaScript Rules for Django Projects

> Rules for `*.js` files in a Django + Tailwind CSS + Vanilla JS + Django Templates stack.
> No frontend framework (React, Vue, etc.). No jQuery. No TypeScript. ES2022+ only.

## Core Principles

- Write modern Vanilla JavaScript (ES2022+). No frameworks, no jQuery.
- JavaScript enhances Django-rendered HTML — it does not replace it.
- Django templates are the source of truth for HTML structure.
- Use `data-*` attributes as the contract between Django templates and JavaScript.
- Keep JavaScript files small, focused, and modular.

## File Organization

### Directory Structure

```
static/
├── js/
│   ├── modules/              # Reusable ES modules
│   │   ├── csrf.js           # CSRF token utility
│   │   ├── api.js            # Fetch wrapper with CSRF
│   │   ├── toast.js          # Toast notification component
│   │   └── modal.js          # Modal dialog component
│   ├── pages/                # Page-specific scripts
│   │   ├── dashboard.js      # Dashboard page behavior
│   │   ├── user-list.js      # User list page behavior
│   │   └── settings.js       # Settings page behavior
│   └── main.js               # Global entry point (shared across all pages)
├── css/
│   └── input.css             # Tailwind CSS input file
└── dist/                     # Built assets (gitignored in dev)
```

### Naming Conventions

| Target | Convention | Example |
|--------|-----------|---------|
| File | `kebab-case.js` | `user-list.js`, `csrf.js` |
| Module file | `kebab-case.js` | `toast.js`, `api.js` |
| Function | `camelCase` | `fetchUsers()`, `handleSubmit()` |
| Class | `PascalCase` | `ToastNotification`, `ModalDialog` |
| Constant | `UPPER_SNAKE_CASE` | `API_BASE_URL`, `MAX_RETRIES` |
| Private | `_` prefix or `#` private field | `_internalState`, `#count` |
| Event handler | `handle` + Event | `handleClick()`, `handleSubmit()` |
| DOM query | `el` or `$` prefix | `elButton`, `$form` |
| Boolean | `is`/`has`/`can` prefix | `isLoading`, `hasError` |
| `data-*` attribute | `kebab-case` | `data-user-id`, `data-action` |

## ES Modules

### Use Native ES Modules

```html
<!-- Django template -->
{% load static %}
<script type="module" src="{% static 'js/pages/dashboard.js' %}"></script>
```

```javascript
// static/js/pages/dashboard.js
import { apiFetch } from "../modules/api.js";
import { showToast } from "../modules/toast.js";

/**
 * Initialize the dashboard page.
 *
 * Binds event listeners to dashboard-specific elements
 * identified by data-* attributes.
 *
 * @example
 * // Called automatically on module load
 * // Requires: <div data-dashboard-stats-url="/api/stats/"></div>
 */
function init() {
  const elStats = document.querySelector("[data-dashboard-stats-url]");
  if (!elStats) return;

  loadStats(elStats.dataset.dashboardStatsUrl);
}

init();
```

- Always use `type="module"` in script tags.
- Use explicit `.js` extensions in import paths.
- Modules are deferred by default — no need for `defer` attribute.
- Avoid bare specifiers (e.g., `import { x } from "lodash"`) unless using importmap.

### Module Export Rules

```javascript
// Good — named exports for utilities
export function getCsrfToken() { ... }
export function apiFetch(url, options) { ... }

// Good — default export for page initializers or classes
export default class ModalDialog { ... }

// Bad — namespace export objects
export const utils = { getCsrfToken, apiFetch };
```

- Prefer named exports for utility modules.
- Use default exports only for single-purpose modules (page init, component class).

## Django Template ↔ JavaScript Contract

### Use `data-*` Attributes for Communication

```html
<!-- Django template: pass data to JS via data-* attributes -->
<button
  data-action="delete-user"
  data-user-id="{{ user.pk }}"
  data-confirm-message="Delete {{ user.username }}?"
  data-url="{% url 'user-delete' user.pk %}"
>
  Delete
</button>

<div
  data-component="user-list"
  data-api-url="{% url 'api:user-list' %}"
  data-page-size="25"
>
</div>
```

```javascript
// JavaScript reads from data-* attributes — never hardcode URLs or IDs
const elButton = document.querySelector("[data-action='delete-user']");
const userId = elButton.dataset.userId;        // "42"
const url = elButton.dataset.url;              // "/users/42/delete/"
const message = elButton.dataset.confirmMessage; // "Delete johndoe?"
```

### Rules

- **Never** hardcode Django URLs in JavaScript. Always pass via `data-url` or `data-api-url`.
- **Never** hardcode Django model PKs in JavaScript. Always pass via `data-*-id`.
- **Never** embed `{% url %}` tags inside `.js` files. Django templates cannot process static JS files.
- Use `data-component` to identify top-level interactive sections.
- Use `data-action` to identify clickable/interactive elements.

### Passing Complex Data

For structured data, use `json_script`:

```html
<!-- Django template -->
{{ chart_data|json_script:"chart-config" }}

<canvas data-component="chart" data-config-id="chart-config"></canvas>
```

```javascript
// JavaScript
const elChart = document.querySelector("[data-component='chart']");
const configId = elChart.dataset.configId;
const config = JSON.parse(document.getElementById(configId).textContent);
```

- Use Django's `json_script` template tag for complex/large data.
- Connects to JS via a shared element ID referenced in `data-config-id`.

## CSRF Token Handling

### CSRF Utility Module

```javascript
// static/js/modules/csrf.js

/**
 * Get the CSRF token from the cookie.
 *
 * Django sets a `csrftoken` cookie by default. This function
 * reads it for use in fetch requests.
 *
 * @returns {string} The CSRF token value.
 * @throws {Error} If the CSRF cookie is not found.
 *
 * @example
 * const token = getCsrfToken();
 * // "abc123..."
 */
export function getCsrfToken() {
  const cookie = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="));

  if (!cookie) {
    throw new Error("CSRF cookie not found. Ensure {% csrf_token %} is in the template.");
  }
  return cookie.split("=")[1];
}
```

### Fetch Wrapper with CSRF

```javascript
// static/js/modules/api.js
import { getCsrfToken } from "./csrf.js";

/**
 * Fetch wrapper with automatic CSRF token and JSON handling.
 *
 * @param {string} url - The API endpoint URL.
 * @param {Object} [options={}] - Fetch options.
 * @param {string} [options.method="GET"] - HTTP method.
 * @param {Object} [options.body] - Request body (auto-serialized to JSON).
 * @param {Object} [options.headers] - Additional headers.
 * @returns {Promise<Object>} Parsed JSON response.
 * @throws {ApiError} If the response status is not ok.
 *
 * @example
 * // GET request
 * const users = await apiFetch("/api/users/");
 *
 * @example
 * // POST request
 * const newUser = await apiFetch("/api/users/", {
 *   method: "POST",
 *   body: { username: "john", email: "john@example.com" },
 * });
 *
 * @example
 * // DELETE request
 * await apiFetch("/api/users/42/", { method: "DELETE" });
 */
export async function apiFetch(url, options = {}) {
  const { method = "GET", body, headers = {}, ...rest } = options;

  const config = {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
      ...headers,
    },
    credentials: "same-origin",
    ...rest,
  };

  if (body && method !== "GET") {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(url, config);

  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }

  if (response.status === 204) return null;
  return response.json();
}

/**
 * API error with status code and response body.
 *
 * @example
 * try {
 *   await apiFetch("/api/users/999/");
 * } catch (error) {
 *   if (error instanceof ApiError && error.status === 404) {
 *     showToast("User not found", "error");
 *   }
 * }
 */
export class ApiError extends Error {
  /**
   * @param {number} status - HTTP status code.
   * @param {string} body - Response body text.
   */
  constructor(status, body) {
    super(`API error ${status}: ${body}`);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}
```

## Event Handling

### Event Delegation

Use event delegation for dynamically rendered or repeated elements:

```javascript
/**
 * Initialize event delegation for user action buttons.
 *
 * Uses a single listener on the container instead of per-button
 * listeners. Handles click events based on data-action attributes.
 *
 * @param {HTMLElement} elContainer - The container element.
 *
 * @example
 * // HTML:
 * // <div data-component="user-list">
 * //   <button data-action="edit" data-user-id="1">Edit</button>
 * //   <button data-action="delete" data-user-id="1">Delete</button>
 * // </div>
 *
 * const el = document.querySelector("[data-component='user-list']");
 * initUserActions(el);
 */
function initUserActions(elContainer) {
  elContainer.addEventListener("click", (event) => {
    const elTarget = event.target.closest("[data-action]");
    if (!elTarget) return;

    const action = elTarget.dataset.action;
    const userId = elTarget.dataset.userId;

    switch (action) {
      case "edit":
        handleEdit(userId);
        break;
      case "delete":
        handleDelete(userId, elTarget.dataset.url);
        break;
      default:
        console.warn(`Unknown action: ${action}`);
    }
  });
}
```

### Rules

- Use event delegation on container elements, not individual items.
- Use `.closest("[data-action]")` to find the action trigger.
- Never use inline `onclick` attributes in Django templates.
- Remove event listeners when elements are destroyed (`AbortController`).

```javascript
/**
 * Set up an abortable event listener.
 *
 * @example
 * const controller = new AbortController();
 * document.addEventListener("click", handleClick, { signal: controller.signal });
 * // Later: controller.abort(); // removes the listener
 */
```

## DOM Manipulation

### Query Selectors

```javascript
// Good — query by data-* attribute
const elForm = document.querySelector("[data-component='login-form']");
const elButtons = document.querySelectorAll("[data-action='submit']");

// Acceptable — query by ID for unique elements
const elNav = document.getElementById("main-nav");

// Bad — query by Tailwind CSS classes (fragile, classes change)
const elForm = document.querySelector(".bg-white.rounded-lg.shadow");

// Bad — query by tag structure (fragile)
const elButton = document.querySelector("div > form > button:first-child");
```

### Rules

- **Always** select elements by `data-*` attributes or IDs.
- **Never** select elements by Tailwind CSS utility classes — they are styling, not identity.
- **Never** use complex structural selectors — templates change frequently.
- Cache DOM queries in variables; don't re-query inside loops or handlers.

### Dynamic HTML

```javascript
// Good — template literals for small fragments
function createUserRow(user) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td class="px-4 py-2">${escapeHtml(user.name)}</td>
    <td class="px-4 py-2">${escapeHtml(user.email)}</td>
    <td class="px-4 py-2">
      <button data-action="edit" data-user-id="${user.id}"
              class="text-blue-600 hover:text-blue-800">Edit</button>
    </td>
  `;
  return tr;
}

// Good — <template> element for complex fragments
// In Django template:
// <template id="user-row-template">
//   <tr>
//     <td class="px-4 py-2" data-field="name"></td>
//     <td class="px-4 py-2" data-field="email"></td>
//   </tr>
// </template>

function createUserRowFromTemplate(user) {
  const template = document.getElementById("user-row-template");
  const clone = template.content.cloneNode(true);
  clone.querySelector("[data-field='name']").textContent = user.name;
  clone.querySelector("[data-field='email']").textContent = user.email;
  return clone;
}
```

### XSS Prevention

```javascript
/**
 * Escape HTML special characters to prevent XSS.
 *
 * @param {string} str - The string to escape.
 * @returns {string} The escaped string safe for innerHTML.
 *
 * @example
 * escapeHtml('<script>alert("xss")</script>')
 * // "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;"
 *
 * @example
 * escapeHtml("Hello & 'world'")
 * // "Hello &amp; &#x27;world&#x27;"
 */
export function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
```

- **Always** escape user-generated content when using `innerHTML`.
- Prefer `textContent` over `innerHTML` when no HTML is needed.
- Use `<template>` elements + `textContent` for the safest approach.
- Never use `eval()`, `new Function()`, or `document.write()`.

## Tailwind CSS Integration

### JavaScript and Tailwind Classes

```javascript
// Good — toggle predefined Tailwind utility classes
function toggleLoading(elButton, isLoading) {
  elButton.disabled = isLoading;
  elButton.classList.toggle("opacity-50", isLoading);
  elButton.classList.toggle("cursor-not-allowed", isLoading);
  elButton.textContent = isLoading ? "Loading..." : "Submit";
}

// Good — use data-state for complex state-driven styling
function setFormState(elForm, state) {
  elForm.dataset.state = state; // "idle" | "loading" | "error" | "success"
}
// Tailwind CSS uses data-state in the template:
// <form data-state="idle" class="data-[state=loading]:opacity-50 data-[state=error]:border-red-500">
```

### Rules

- Toggle Tailwind classes via `classList.add()`/`remove()`/`toggle()`.
- For complex states, set `data-state` and handle styling in CSS/Tailwind with `data-[state=*]:`.
- Never construct Tailwind class names dynamically (e.g., `` `bg-${color}-500` ``). Tailwind's purge cannot detect them.
- Define all possible Tailwind classes in the Django template; JS only toggles them.

### Safelist (for dynamic classes)

If dynamic classes are unavoidable, add them to `tailwind.config.js` safelist:

```javascript
// tailwind.config.js
module.exports = {
  safelist: [
    "bg-green-100", "bg-red-100", "bg-yellow-100",
    "text-green-800", "text-red-800", "text-yellow-800",
  ],
};
```

## Async Patterns

### Loading States

```javascript
/**
 * Execute an async action with loading state management.
 *
 * Disables the button, shows a loading indicator, and re-enables
 * on completion or error.
 *
 * @param {HTMLButtonElement} elButton - The button to manage.
 * @param {Function} action - The async action to execute.
 * @returns {Promise<*>} The result of the action.
 *
 * @example
 * const elSave = document.querySelector("[data-action='save']");
 * elSave.addEventListener("click", () => {
 *   withLoading(elSave, () => apiFetch("/api/save/", { method: "POST" }));
 * });
 */
async function withLoading(elButton, action) {
  const originalText = elButton.textContent;
  elButton.disabled = true;
  elButton.textContent = "Loading...";
  elButton.classList.add("opacity-50", "cursor-not-allowed");

  try {
    return await action();
  } finally {
    elButton.disabled = false;
    elButton.textContent = originalText;
    elButton.classList.remove("opacity-50", "cursor-not-allowed");
  }
}
```

### Error Handling

```javascript
/**
 * Standard error handler for API calls in page scripts.
 *
 * @param {Error} error - The caught error.
 *
 * @example
 * try {
 *   await apiFetch("/api/users/");
 * } catch (error) {
 *   handleApiError(error);
 * }
 */
function handleApiError(error) {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 403:
        showToast("Permission denied", "error");
        break;
      case 404:
        showToast("Resource not found", "error");
        break;
      case 422:
        showFormErrors(JSON.parse(error.body));
        break;
      default:
        showToast("An error occurred. Please try again.", "error");
    }
  } else {
    console.error("Unexpected error:", error);
    showToast("Network error. Check your connection.", "error");
  }
}
```

## Form Handling

```javascript
/**
 * Initialize a Django form with AJAX submission.
 *
 * Intercepts form submit, sends data via fetch with CSRF,
 * and handles validation errors from Django.
 *
 * @param {HTMLFormElement} elForm - The form element with data-ajax-url.
 *
 * @example
 * // HTML:
 * // <form data-component="ajax-form" data-ajax-url="{% url 'user-create' %}">
 * //   {% csrf_token %}
 * //   {{ form.as_div }}
 * //   <button type="submit">Create</button>
 * // </form>
 *
 * const elForm = document.querySelector("[data-component='ajax-form']");
 * initAjaxForm(elForm);
 */
function initAjaxForm(elForm) {
  elForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const elSubmit = elForm.querySelector("[type='submit']");

    await withLoading(elSubmit, async () => {
      const formData = new FormData(elForm);

      const response = await fetch(elForm.dataset.ajaxUrl, {
        method: "POST",
        headers: { "X-CSRFToken": getCsrfToken() },
        credentials: "same-origin",
        body: formData, // Send as FormData, not JSON
      });

      if (response.ok) {
        const data = await response.json();
        showToast("Saved successfully", "success");
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        }
      } else if (response.status === 422) {
        const errors = await response.json();
        showFormErrors(elForm, errors);
      } else {
        throw new ApiError(response.status, await response.text());
      }
    });
  });
}
```

### Rules

- Use `FormData` for Django forms (not JSON) to preserve file uploads and CSRF.
- Send JSON only for API-style endpoints that expect `application/json`.
- Always include `credentials: "same-origin"` for cookie-based auth.
- Handle Django's validation error format (field-level errors).

## Documentation (JSDoc)

All functions must have JSDoc documentation with `@example`:

```javascript
/**
 * Summary line describing what the function does.
 *
 * Optional extended description for complex logic.
 *
 * @param {string} name - Description of the parameter.
 * @param {Object} [options={}] - Optional parameter with default.
 * @param {number} [options.timeout=30] - Timeout in seconds.
 * @returns {Promise<Object>} Description of return value.
 * @throws {ApiError} When the API returns a non-ok response.
 *
 * @example
 * // Basic usage
 * const result = await myFunction("test");
 * // { success: true }
 *
 * @example
 * // With options
 * const result = await myFunction("test", { timeout: 60 });
 */
```

### Required Sections

1. **Summary** (first line, required)
2. **`@param`** (required if parameters exist)
3. **`@returns`** (required if return value exists)
4. **`@throws`** (required if exceptions are thrown)
5. **`@example`** (required — at least one concrete input/output example)

## Error Prevention

### Strict Mode

ES modules are strict by default. For non-module scripts:

```javascript
"use strict";
```

### Null Safety

```javascript
// Good — optional chaining + nullish coalescing
const name = user?.profile?.name ?? "Anonymous";
const count = elContainer?.children?.length ?? 0;

// Good — early return for missing elements
const elWidget = document.querySelector("[data-component='widget']");
if (!elWidget) return;  // Page doesn't have this component
```

### No Global Pollution

```javascript
// Good — module scope (automatic with type="module")
const state = { count: 0 };
export function increment() { state.count++; }

// Bad — attaching to window
window.myApp = { count: 0 };

// Bad — implicit global
count = 0;  // Missing const/let
```

## Linting (ESLint)

Recommended ESLint configuration:

```json
{
  "env": {
    "browser": true,
    "es2022": true
  },
  "parserOptions": {
    "ecmaVersion": 2022,
    "sourceType": "module"
  },
  "extends": ["eslint:recommended"],
  "rules": {
    "no-var": "error",
    "prefer-const": "error",
    "prefer-template": "error",
    "no-eval": "error",
    "no-implied-eval": "error",
    "no-new-func": "error",
    "eqeqeq": ["error", "always"],
    "no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "no-console": ["warn", { "allow": ["warn", "error"] }],
    "curly": ["error", "multi-line"],
    "no-implicit-globals": "error"
  }
}
```

## Prohibited

- No jQuery or any DOM manipulation library.
- No frontend frameworks (React, Vue, Angular, Svelte, etc.).
- No TypeScript (vanilla JS only in this stack).
- No `var` — use `const` by default, `let` only when reassignment is needed.
- No `==` — always use `===` (strict equality).
- No hardcoded Django URLs in `.js` files.
- No hardcoded model PKs or Django template variables in `.js` files.
- No inline `onclick`/`onsubmit` handlers in Django templates.
- No selecting DOM elements by Tailwind CSS utility classes.
- No dynamically constructing Tailwind class names (breaks purge).
- No `eval()`, `new Function()`, or `document.write()`.
- No `innerHTML` with unescaped user input.
- No global variables — everything must be module-scoped.
- No `console.log()` in committed code (use `console.warn()`/`console.error()` for genuine issues).
- No synchronous `XMLHttpRequest` — use `fetch()` with async/await.
