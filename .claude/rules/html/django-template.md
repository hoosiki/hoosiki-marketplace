---
paths:
  - "**/*.html"
  - "**/templates/**"
  - "**/jinja2/**"
---

# Django Template + Tailwind CSS + HTMX Rules

> Rules for `*.html` files in a Django + Tailwind CSS + HTMX + Vanilla JS stack.
> Django templates are the single source of truth for HTML structure and server-rendered content.

## Core Principles

- Django templates own all HTML structure — JavaScript only enhances behavior.
- HTMX handles dynamic server interactions — avoid writing fetch/AJAX in JavaScript.
- Tailwind CSS handles all styling — no custom CSS unless absolutely necessary.
- Semantic HTML first, then layer on Tailwind classes and HTMX attributes.
- Progressive enhancement: pages must work without JavaScript where possible.

## Template Directory Structure

```
app_name/
├── templates/
│   └── app_name/
│       ├── base.html                  # App-level base (extends project base)
│       ├── pages/                     # Full page templates
│       │   ├── dashboard.html
│       │   ├── user_list.html
│       │   └── user_detail.html
│       ├── partials/                  # HTMX partial fragments
│       │   ├── _user_row.html
│       │   ├── _user_form.html
│       │   ├── _toast.html
│       │   └── _search_results.html
│       ├── components/                # Reusable UI components
│       │   ├── _pagination.html
│       │   ├── _modal.html
│       │   ├── _card.html
│       │   └── _empty_state.html
│       └── includes/                  # Structural includes
│           ├── _navbar.html
│           ├── _sidebar.html
│           └── _footer.html
```

### Naming Conventions

| Target | Convention | Example |
|--------|-----------|---------|
| Full page template | `snake_case.html` | `user_list.html`, `dashboard.html` |
| Partial / fragment | `_snake_case.html` (underscore prefix) | `_user_row.html`, `_toast.html` |
| Component | `_snake_case.html` (underscore prefix) | `_modal.html`, `_card.html` |
| Directory | `snake_case/` | `pages/`, `partials/`, `components/` |
| Block name | `snake_case` | `{% block page_title %}`, `{% block content %}` |

### Rules

- Full pages go in `pages/` — these extend a base template.
- HTMX fragments go in `partials/` — these return HTML snippets, NOT full pages.
- Reusable UI components go in `components/` — used via `{% include %}`.
- All partials and components use the `_` prefix to distinguish them from full pages.
- Template directories mirror Django app names: `templates/app_name/`.

## Template Inheritance

### Base Template

```html
{# templates/base.html #}
{% load static %}
<!DOCTYPE html>
<html lang="ko" class="h-full">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}{% block page_title %}{% endblock %} | Site Name{% endblock %}</title>

  {# Tailwind CSS #}
  <link rel="stylesheet" href="{% static 'css/output.css' %}">

  {# HTMX #}
  <script src="{% static 'js/vendor/htmx.min.js' %}" defer></script>

  {% block extra_head %}{% endblock %}
</head>
<body class="h-full bg-gray-50 text-gray-900"
      hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

  {% include "includes/_navbar.html" %}

  <main class="container mx-auto px-4 py-8">
    {# Django messages as HTMX-compatible toasts #}
    <div id="toast-container" class="fixed top-4 right-4 z-50 space-y-2">
      {% for message in messages %}
        {% include "components/_toast.html" with message=message %}
      {% endfor %}
    </div>

    {% block content %}{% endblock %}
  </main>

  {% include "includes/_footer.html" %}

  {# Global JS (shared utilities) #}
  <script type="module" src="{% static 'js/main.js' %}"></script>
  {% block extra_js %}{% endblock %}
</body>
</html>
```

### Rules

- Every page template must `{% extends %}` a base template.
- Use `{% block %}` for content injection — never duplicate layout HTML.
- Keep blocks granular: `title`, `page_title`, `content`, `extra_head`, `extra_js`.
- The `extra_js` block is for page-specific scripts only.
- CSRF token is set globally via `hx-headers` on `<body>` — no per-request CSRF needed for HTMX.

### Page Template

```html
{# templates/app_name/pages/user_list.html #}
{% extends "base.html" %}
{% load static %}

{% block page_title %}Users{% endblock %}

{% block content %}
<div class="space-y-6">
  <header class="flex items-center justify-between">
    <h1 class="text-2xl font-bold text-gray-900">Users</h1>
    <button
      hx-get="{% url 'user-create-form' %}"
      hx-target="#modal-container"
      hx-swap="innerHTML"
      class="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
    >
      Add User
    </button>
  </header>

  {# Search with HTMX #}
  <input
    type="search"
    name="q"
    placeholder="Search users..."
    hx-get="{% url 'user-search' %}"
    hx-trigger="input changed delay:300ms, search"
    hx-target="#user-list"
    hx-swap="innerHTML"
    hx-indicator="#search-spinner"
    class="w-full rounded-md border border-gray-300 px-4 py-2"
  >
  <span id="search-spinner" class="htmx-indicator">Searching...</span>

  {# User list (swappable by HTMX) #}
  <div id="user-list">
    {% include "app_name/partials/_user_list_body.html" %}
  </div>

  {# Modal container (empty, filled by HTMX) #}
  <div id="modal-container"></div>
</div>
{% endblock %}

{% block extra_js %}
<script type="module" src="{% static 'js/pages/user-list.js' %}"></script>
{% endblock %}
```

## HTMX Patterns

### Core HTMX Attributes

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `hx-get` | GET request | `hx-get="{% url 'user-list' %}"` |
| `hx-post` | POST request | `hx-post="{% url 'user-create' %}"` |
| `hx-put` | PUT request | `hx-put="{% url 'user-update' pk=user.pk %}"` |
| `hx-delete` | DELETE request | `hx-delete="{% url 'user-delete' pk=user.pk %}"` |
| `hx-target` | Where to put response | `hx-target="#user-list"` |
| `hx-swap` | How to swap content | `hx-swap="innerHTML"`, `outerHTML`, `beforeend` |
| `hx-trigger` | When to fire | `hx-trigger="click"`, `input changed delay:300ms` |
| `hx-indicator` | Loading indicator | `hx-indicator="#spinner"` |
| `hx-confirm` | Confirmation dialog | `hx-confirm="Delete this user?"` |
| `hx-push-url` | Update browser URL | `hx-push-url="true"` |
| `hx-boost` | Progressive enhancement | `hx-boost="true"` on `<a>` or `<form>` |

### Partial Templates (HTMX Fragments)

```html
{# templates/app_name/partials/_user_row.html #}
{# This returns a single <tr>, not a full page #}
<tr id="user-row-{{ user.pk }}" class="border-b border-gray-200 hover:bg-gray-50">
  <td class="px-4 py-3 text-sm">{{ user.username }}</td>
  <td class="px-4 py-3 text-sm">{{ user.email }}</td>
  <td class="px-4 py-3 text-sm">
    <span class="inline-flex rounded-full px-2 text-xs font-semibold
      {% if user.is_active %}bg-green-100 text-green-800{% else %}bg-red-100 text-red-800{% endif %}">
      {% if user.is_active %}Active{% else %}Inactive{% endif %}
    </span>
  </td>
  <td class="px-4 py-3 text-sm text-right space-x-2">
    <button
      hx-get="{% url 'user-edit-form' pk=user.pk %}"
      hx-target="#modal-container"
      hx-swap="innerHTML"
      class="text-blue-600 hover:text-blue-800"
    >
      Edit
    </button>
    <button
      hx-delete="{% url 'user-delete' pk=user.pk %}"
      hx-target="#user-row-{{ user.pk }}"
      hx-swap="outerHTML swap:500ms"
      hx-confirm="Delete {{ user.username }}?"
      class="text-red-600 hover:text-red-800"
    >
      Delete
    </button>
  </td>
</tr>
```

### Rules

- Partials return **only the fragment** — never `<!DOCTYPE>`, `<html>`, `<head>`, or `<body>`.
- Each swappable element must have a unique `id` (e.g., `id="user-row-{{ user.pk }}"`).
- Use `hx-target` with `#id` selectors — never target by CSS class.
- Use `hx-swap="outerHTML"` when replacing the element itself, `innerHTML` when replacing children.
- Use `hx-trigger="input changed delay:300ms"` for search inputs to debounce.
- Always include `hx-confirm` for destructive actions (delete, archive).

### Out-of-Band (OOB) Swaps

Update multiple parts of the page from a single response:

```html
{# View returns this partial after creating a user #}

{# Primary response: new row appended to the table #}
<tr id="user-row-{{ user.pk }}" class="border-b border-gray-200">
  <td class="px-4 py-3">{{ user.username }}</td>
  {# ... #}
</tr>

{# OOB swap: update the user count badge #}
<span id="user-count" hx-swap-oob="innerHTML">
  {{ total_users }}
</span>

{# OOB swap: show success toast #}
<div id="toast-container" hx-swap-oob="beforeend">
  {% include "components/_toast.html" with message="User created" level="success" %}
</div>
```

### Rules for OOB

- Use `hx-swap-oob="innerHTML"` or `hx-swap-oob="beforeend"` on secondary elements.
- OOB elements must have matching `id` attributes in the current page.
- Limit OOB swaps to 2-3 per response — more indicates the page needs a full reload.

### HTMX Form Pattern

```html
{# templates/app_name/partials/_user_form.html #}
<form
  hx-post="{% url 'user-create' %}"
  hx-target="#user-list"
  hx-swap="beforeend"
  hx-on::after-request="if(event.detail.successful) closeModal()"
  class="space-y-4"
>
  {% csrf_token %}

  <div>
    <label for="id_username" class="block text-sm font-medium text-gray-700">Username</label>
    {{ form.username }}
    {% if form.username.errors %}
      <p class="mt-1 text-sm text-red-600">{{ form.username.errors.0 }}</p>
    {% endif %}
  </div>

  <div>
    <label for="id_email" class="block text-sm font-medium text-gray-700">Email</label>
    {{ form.email }}
    {% if form.email.errors %}
      <p class="mt-1 text-sm text-red-600">{{ form.email.errors.0 }}</p>
    {% endif %}
  </div>

  <div class="flex justify-end space-x-3">
    <button type="button" onclick="closeModal()"
            class="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
      Cancel
    </button>
    <button type="submit"
            class="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
      Save
    </button>
  </div>
</form>
```

### Rules for Forms

- Include `{% csrf_token %}` inside every `<form>` — even with body-level `hx-headers`.
- On validation error, the Django view should re-render the form partial with errors.
- On success, return the new/updated fragment (not a redirect).
- Use `hx-on::after-request` for post-submission actions (close modal, reset form).

## Tailwind CSS in Templates

### Class Organization

Order Tailwind classes consistently (layout → sizing → spacing → typography → visual → state):

```html
{# Good — organized order #}
<div class="flex items-center justify-between w-full max-w-lg mx-auto px-4 py-2 text-sm font-medium text-gray-900 bg-white rounded-lg shadow-sm hover:bg-gray-50">

{# Pattern: layout → sizing → spacing → text → bg/border → effects → states #}
```

### Responsive Design

```html
{# Mobile-first with breakpoint prefixes #}
<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
  {% for item in items %}
    {% include "components/_card.html" with item=item %}
  {% endfor %}
</div>

{# Hide/show by breakpoint #}
<nav class="hidden lg:block">Desktop nav</nav>
<nav class="block lg:hidden">Mobile nav</nav>
```

### Component with Tailwind

```html
{# templates/components/_card.html #}
{# Usage: {% include "components/_card.html" with title="..." body="..." %} #}
<article class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition hover:shadow-md">
  {% if image_url %}
    <img src="{{ image_url }}" alt="{{ title }}" class="h-48 w-full object-cover">
  {% endif %}
  <div class="p-4 space-y-2">
    <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
    {% if body %}
      <p class="text-sm text-gray-600 line-clamp-3">{{ body }}</p>
    {% endif %}
    {% if action_url %}
      <a href="{{ action_url }}"
         class="inline-block text-sm font-medium text-blue-600 hover:text-blue-800">
        {{ action_text|default:"View details" }} &rarr;
      </a>
    {% endif %}
  </div>
</article>
```

### Rules

- Never use `style=""` inline styles — use Tailwind utility classes.
- Never create custom CSS for what Tailwind can handle.
- Use `@apply` sparingly and only in `input.css` for frequently repeated patterns.
- All color/spacing/typography values must come from the Tailwind config — no arbitrary values unless necessary (e.g., `w-[calc(100%-2rem)]`).
- Use Tailwind's `data-*` variant for state-driven styling: `data-[state=active]:bg-blue-500`.

## Semantic HTML

### Use Correct Elements

```html
{# Good — semantic elements #}
<header>...</header>
<nav aria-label="Main navigation">...</nav>
<main>
  <section aria-labelledby="users-heading">
    <h2 id="users-heading">Users</h2>
    <table>...</table>
  </section>
</main>
<aside>...</aside>
<footer>...</footer>

{# Bad — div soup #}
<div class="header">...</div>
<div class="nav">...</div>
<div class="main">
  <div class="section">
    <div class="title">Users</div>
    <div class="table">...</div>
  </div>
</div>
```

### Heading Hierarchy

```html
{# Good — sequential heading levels #}
<h1>Dashboard</h1>
  <h2>Recent Activity</h2>
    <h3>Today</h3>
    <h3>Yesterday</h3>
  <h2>Statistics</h2>

{# Bad — skipping levels #}
<h1>Dashboard</h1>
  <h4>Recent Activity</h4>  {# Skipped h2, h3 #}
```

### Accessibility

```html
{# Buttons vs Links #}
<a href="{% url 'user-detail' pk=user.pk %}">View Profile</a>     {# Navigation → <a> #}
<button hx-post="{% url 'user-delete' pk=user.pk %}">Delete</button> {# Action → <button> #}

{# ARIA attributes #}
<button aria-label="Close modal" aria-expanded="false">
  <svg>...</svg>  {# Icon-only button needs aria-label #}
</button>

{# Loading states #}
<div id="user-list" aria-live="polite" aria-busy="false">
  {# HTMX updates announce to screen readers #}
</div>

{# Form accessibility #}
<label for="id_email">Email</label>
<input id="id_email" type="email" name="email" required
       aria-describedby="email-help"
       aria-invalid="{% if form.email.errors %}true{% else %}false{% endif %}">
<p id="email-help" class="text-sm text-gray-500">We'll never share your email.</p>
{% if form.email.errors %}
  <p role="alert" class="text-sm text-red-600">{{ form.email.errors.0 }}</p>
{% endif %}
```

### Rules

- Use `<a>` for navigation, `<button>` for actions — never the reverse.
- Every `<img>` must have an `alt` attribute (empty `alt=""` for decorative images).
- Icon-only buttons must have `aria-label`.
- Form inputs must have associated `<label>` elements.
- Use `aria-live="polite"` on HTMX target containers for screen reader announcements.
- Use `role="alert"` on form error messages.
- Heading levels must not skip (h1 → h2 → h3, not h1 → h4).

## Django Template Tags

### Preferred Patterns

```html
{# Variable output — auto-escaped by Django #}
{{ user.username }}
{{ user.get_full_name }}

{# URL resolution — always use {% url %} #}
<a href="{% url 'user-detail' pk=user.pk %}">{{ user.username }}</a>

{# Static files — always use {% static %} #}
<img src="{% static 'img/logo.svg' %}" alt="Logo">

{# Conditional rendering #}
{% if user.is_active %}
  <span class="text-green-600">Active</span>
{% elif user.is_staff %}
  <span class="text-yellow-600">Staff</span>
{% else %}
  <span class="text-red-600">Inactive</span>
{% endif %}

{# Loop with empty fallback #}
{% for user in users %}
  {% include "app_name/partials/_user_row.html" with user=user %}
{% empty %}
  {% include "components/_empty_state.html" with message="No users found" %}
{% endfor %}

{# Complex data to JS — use json_script #}
{{ chart_data|json_script:"chart-data" }}

{# Include with explicit context #}
{% include "components/_card.html" with title=item.title body=item.description only %}
```

### Rules

- Always use `{% url %}` for URLs — never hardcode paths.
- Always use `{% static %}` for static files.
- Use `{% include ... with ... only %}` to restrict context (prevent leaking variables).
- Use `{% empty %}` in `{% for %}` loops to handle empty lists.
- Use `{{ value|json_script:"id" }}` to pass data to JavaScript — never embed in `<script>`.
- Avoid complex logic in templates — move to template tags, filters, or the view.
- Never use `{{ value|safe }}` or `{% autoescape off %}` unless absolutely necessary and the value is trusted.

### Template Comments

```html
{# Single line comment — not rendered in output #}

{#
  Multi-line comment for complex explanations.
  Describe WHY, not WHAT — the template structure should be self-evident.
#}

<!-- HTML comment — rendered in output, visible in source. Avoid in production. -->
```

- Use `{# #}` for template comments (not rendered in HTML output).
- Avoid `<!-- -->` HTML comments — they increase page size and expose internals.

## HTMX + JavaScript Integration

### When to Use HTMX vs JavaScript

| Use Case | Use HTMX | Use Vanilla JS |
|----------|----------|---------------|
| Fetch and render server HTML | Yes | No |
| Form submission with validation | Yes | No |
| Inline editing | Yes | No |
| Search with debounce | Yes | No |
| Client-side animations | No | Yes |
| Copy to clipboard | No | Yes |
| Local state (dropdown, tab) | No | Yes |
| Drag and drop | No | Yes |
| Complex client-only calculation | No | Yes |

### HTMX Events in JavaScript

```html
<div id="user-list"
     data-component="user-list"
     hx-get="{% url 'user-list' %}"
     hx-trigger="load">
</div>
```

```javascript
// Listen to HTMX events in JavaScript
document.body.addEventListener("htmx:afterSwap", (event) => {
  // Re-initialize JS components after HTMX swaps new content
  if (event.detail.target.id === "user-list") {
    initSortableTable(event.detail.target);
  }
});

document.body.addEventListener("htmx:beforeRequest", (event) => {
  // Show global loading indicator
});

document.body.addEventListener("htmx:responseError", (event) => {
  // Handle HTMX request errors
  showToast("Request failed. Please try again.", "error");
});
```

### Rules

- Use HTMX for **server-rendered content** — it replaces fetch/AJAX for most use cases.
- Use Vanilla JS only for **client-side-only behavior** (animations, clipboard, local state).
- Listen to `htmx:afterSwap` to reinitialize JS components on dynamically loaded content.
- Listen to `htmx:responseError` for global error handling.

## Security

### CSRF

```html
{# Option 1: Body-level header (recommended for HTMX) #}
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

{# Option 2: Per-form token (standard Django forms) #}
<form method="post">
  {% csrf_token %}
  ...
</form>
```

### XSS Prevention

- Django auto-escapes all `{{ variable }}` output — do not disable this.
- Never use `{{ value|safe }}` with user-generated content.
- Never use `{% autoescape off %}` blocks with untrusted data.
- Use `{{ value|json_script:"id" }}` to safely pass data to JavaScript.

### Content Security

```html
{# Good — structured data passing #}
{{ user_data|json_script:"user-data" }}
<script type="module">
  const data = JSON.parse(document.getElementById("user-data").textContent);
</script>

{# Bad — inline script with template variables #}
<script>
  const userId = {{ user.pk }};  {# XSS risk if user.pk is manipulated #}
  const name = "{{ user.name }}";  {# XSS risk with quotes #}
</script>
```

## Indentation and Formatting

- Use 2 spaces for HTML indentation.
- Use 2 spaces for Django template tag indentation (align with HTML).
- Align HTMX attributes vertically when there are 3+ attributes.
- Keep one blank line between logical sections.

```html
{# Good — aligned HTMX attributes, clear structure #}
<button
  hx-delete="{% url 'user-delete' pk=user.pk %}"
  hx-target="#user-row-{{ user.pk }}"
  hx-swap="outerHTML swap:500ms"
  hx-confirm="Delete {{ user.username }}?"
  class="text-red-600 hover:text-red-800"
>
  Delete
</button>

{# Bad — all on one line #}
<button hx-delete="{% url 'user-delete' pk=user.pk %}" hx-target="#user-row-{{ user.pk }}" hx-swap="outerHTML swap:500ms" hx-confirm="Delete {{ user.username }}?" class="text-red-600 hover:text-red-800">Delete</button>
```

## Prohibited

- No inline `style=""` attributes — use Tailwind utility classes.
- No inline `onclick`/`onsubmit` JavaScript handlers — use HTMX attributes or `data-action` + JS.
- No hardcoded URLs — always use `{% url %}`.
- No hardcoded static file paths — always use `{% static %}`.
- No `{{ value|safe }}` with user-generated content.
- No `{% autoescape off %}` with untrusted data.
- No `<script>` tags with embedded Django template variables (use `json_script`).
- No `<!-- HTML comments -->` in production templates (use `{# #}`).
- No `<div>` when a semantic element exists (`<nav>`, `<main>`, `<section>`, `<article>`, etc.).
- No heading level skips (h1 → h3 without h2).
- No `<a>` elements for actions — use `<button>`.
- No `<img>` without `alt` attribute.
- No HTMX targeting by CSS class — always use `#id` selectors.
- No fetch/AJAX in JavaScript for operations HTMX can handle.
- No template logic that belongs in views or template tags (keep templates dumb).
