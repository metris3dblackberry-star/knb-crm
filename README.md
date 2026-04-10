<div align="center"><a name="readme-top"></a>

[![Project Banner](./public/RepairOS-logo.svg)](#)

# RepairOS<br/><h3>Multi-Tenant Automotive Repair Management Platform</h3>

A production-ready SaaS platform for automotive repair shop management, featuring multi-tenant architecture with shared-schema isolation, role-based access control, Stripe subscription billing, and a "Precision Industrial" design system.<br/>
Built with **Flask 3.1**, **SQLAlchemy 2.0**, **Neon PostgreSQL**, **Google OAuth**, and **Bootstrap 5.3**.<br/>
One-click deployment to **Heroku** with cloud-native database on **Neon**.

[Live Demo][project-link] · [Documentation](docs/) · [Report Bug][github-issues-link] · [Request Feature][github-issues-link]

<br/>

[![Visit Live Demo](https://img.shields.io/badge/🔧_Visit_Live_Demo-1e3a5f?style=for-the-badge&logoColor=white)][project-link]

<br/>

<!-- SHIELD GROUP -->

[![][python-shield]][python-link]
[![][flask-shield]][flask-link]
[![][sqlalchemy-shield]][sqlalchemy-link]
[![][postgresql-shield]][postgresql-link]
[![][stripe-shield]][stripe-link]
[![][heroku-shield]][heroku-link]
[![][bootstrap-shield]][bootstrap-link]
[![][license-shield]][license-link]

<!-- QUICK ACTION BUTTONS -->

<p align="center">
  <a href="https://github.com/ChanMeng666/automotive-repair-management-system/stargazers">
    <img src="https://img.shields.io/badge/⭐_Star_This_Repo-FFD700?style=for-the-badge&logo=github&logoColor=black" alt="Star this repo"/>
  </a>
</p>

**Share Project Repository**

[![][share-x-shield]][share-x-link]
[![][share-linkedin-shield]][share-linkedin-link]
[![][share-reddit-shield]][share-reddit-link]
[![][share-telegram-shield]][share-telegram-link]

<sup>Built for the next generation of automotive repair shop management.</sup>

**Tech Stack:**

<div align="center">

 <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54"/>
 <img src="https://img.shields.io/badge/flask-%23000000.svg?style=for-the-badge&logo=flask&logoColor=white"/>
 <img src="https://img.shields.io/badge/postgresql-%234169E1.svg?style=for-the-badge&logo=postgresql&logoColor=white"/>
 <img src="https://img.shields.io/badge/stripe-%23635BFF.svg?style=for-the-badge&logo=stripe&logoColor=white"/>
 <img src="https://img.shields.io/badge/bootstrap-%237952B3.svg?style=for-the-badge&logo=bootstrap&logoColor=white"/>
 <img src="https://img.shields.io/badge/heroku-%23430098.svg?style=for-the-badge&logo=heroku&logoColor=white"/>
 <img src="https://img.shields.io/badge/chart.js-%23FF6384.svg?style=for-the-badge&logo=chartdotjs&logoColor=white"/>

</div>

</div>

> [!IMPORTANT]
> This project is a comprehensive multi-tenant SaaS platform that combines Flask backend with a modern Bootstrap 5.3 frontend. It features shared-schema multi-tenancy, 6-role RBAC, Stripe subscription billing, Google OAuth, 4-step onboarding, inventory management, and a full-featured admin/technician portal with real-time analytics.

<details>
<summary><kbd>📑 Table of Contents</kbd></summary>

#### TOC

- [🌟 Introduction](#-introduction)
- [✨ Key Features](#-key-features)
  - [`1` Multi-Tenant SaaS Architecture](#1-multi-tenant-saas-architecture)
  - [`2` Role-Based Dual Portals](#2-role-based-dual-portals)
  - [`3` Stripe Subscription Billing](#3-stripe-subscription-billing)
  - [`*` Additional Features](#-additional-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [🏗️ Architecture](#️-architecture)
- [📊 Database Schema](#-database-schema)
- [🚀 Getting Started](#-getting-started)
- [🛳 Deployment](#-deployment)
- [📖 API Reference](#-api-reference)
- [⌨️ Development](#️-development)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [🙋‍♀️ Author](#️-author)

####

<br/>

</details>

<!-- ═══════════════════════════════════════════════════════════════════════════
     SECTION: Introduction
     ═══════════════════════════════════════════════════════════════════════════ -->

## 🌟 Introduction

<table>
<tr>
<td>

<h4>About This Project</h4>

RepairOS is a production-grade multi-tenant SaaS platform purpose-built for automotive repair shops. It enables repair businesses to manage work orders, customers, billing, inventory, and team members through a single unified platform with complete tenant data isolation.

The platform supports multiple organizations on a shared database schema using `tenant_id` discriminator columns, with automatic query filtering via custom SQLAlchemy mixins. Each organization gets its own isolated workspace with configurable service catalogs, parts inventory, and team roles.

<h4>Why This Project?</h4>

Automotive repair shops often rely on fragmented tools — paper work orders, spreadsheets for billing, separate inventory systems. This platform consolidates all operations into one cohesive system with:

- **Multi-tenant isolation** so multiple shops can share one deployment
- **Role-based access** so technicians and administrators see only what they need
- **Stripe billing** for SaaS monetization with subscription plans
- **4-step onboarding** to get new shops operational in minutes

<h4>Goals</h4>

- Deliver a complete, deployable SaaS reference architecture using Flask
- Demonstrate shared-schema multi-tenancy with automatic data isolation
- Provide a modern, responsive UI following the "Precision Industrial" design language
- Enable one-click cloud deployment with Heroku + Neon PostgreSQL

</td>
</tr>
</table>

> [!NOTE]
> - Python 3.9+ required
> - Neon PostgreSQL account required for cloud database (SQLite used for local testing)
> - Google Cloud Console account optional (for OAuth sign-in)
> - Stripe account optional (for subscription billing)

| [![][demo-shield-badge]][project-link] | No installation required! Visit the live demo to experience it firsthand. |
| :------------------------------------- | :------------------------------------------------------------------------ |

<div align="right">

[![][back-to-top]](#readme-top)

</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     SECTION: Key Features
     ═══════════════════════════════════════════════════════════════════════════ -->

## ✨ Key Features

### `1` Multi-Tenant SaaS Architecture

Complete shared-schema multi-tenancy with automatic data isolation. Each organization operates in its own workspace with independent service catalogs, customer records, and team management — all on a single database deployment.

Key capabilities include:
- 🏢 **Organization Management**: Create and configure multiple repair shops with custom settings
- 🔒 **Data Isolation**: `TenantScopedMixin` automatically filters all queries by `tenant_id`
- 👥 **Team Invitations**: Invite team members with role-based permissions
- 🚀 **4-Step Onboarding**: Guided setup for business details, service catalog, parts catalog, and team
- 🌐 **Tenant-Scoped URLs**: Routes available at both `/technician/...` and `/org/<slug>/technician/...`

[![][back-to-top]](#readme-top)

### `2` Role-Based Dual Portals

Two distinct portal experiences for Technicians and Administrators, controlled by a 6-role RBAC system defined on `TenantMembership`:

**Technician Portal:**
- 📋 Work order management with pagination
- 🔧 Add services and parts to jobs with quantity tracking
- 💰 Real-time total cost calculation
- ✅ Job completion workflow

**Administrator Portal:**
- 👤 Customer management with search (first name, family name, or both)
- 💳 Billing management with overdue tracking (14-day threshold)
- 📦 Service & parts catalog management with categories and descriptions
- 📊 Inventory tracking with reorder alerts and stock adjustments
- 👥 Team member management with role assignment
- 📈 Dashboard with Chart.js analytics (monthly revenue, job status distribution)
- ⚙️ Organization settings and subscription management

**RBAC Roles:**

| Role | Key Permissions |
|------|----------------|
| `owner` | Full access including organization management |
| `admin` | User management, catalog, inventory, jobs, billing, reports |
| `manager` | Jobs, customers, billing, reports |
| `technician` | Jobs, reports |
| `parts_clerk` | Catalog, inventory, reports |
| `viewer` | Reports only |

[![][back-to-top]](#readme-top)

### `3` Stripe Subscription Billing

Integrated SaaS billing with Stripe for subscription management:

- 💎 **4 Plans**: Free, Starter ($29/mo), Professional ($79/mo), Enterprise ($199/mo)
- 🎁 **14-Day Trial**: Free trial period for new organizations
- 🛒 **Stripe Checkout**: Hosted payment pages for secure card processing
- 🔄 **Billing Portal**: Customer self-service for plan changes and payment methods
- 📡 **Webhook Handling**: Automatic subscription status updates on payment events

[![][back-to-top]](#readme-top)

### `*` Additional Features

- [x] 🔐 **Google OAuth 2.0**: One-click sign-in via Authlib integration
- [x] 🔑 **JWT Authentication**: Optional Neon Auth (Better Auth) JWT verification
- [x] 🛡️ **CSRF Protection**: Token-based CSRF on all state-changing requests
- [x] 🧹 **Input Sanitization**: XSS prevention and SQL injection scanning
- [x] 🔒 **Security Headers**: HSTS, X-Frame-Options, X-Content-Type-Options
- [x] 🔐 **Password Security**: PBKDF2 hashing with 100,000 iterations
- [x] 🎨 **Precision Industrial Design**: Steel blue (#1e3a5f) + signal orange (#e85d04) palette
- [x] 📱 **Responsive Layout**: Mobile-first with breakpoints at 768px and 480px
- [x] 📊 **Chart.js Dashboards**: Monthly revenue line charts, job status doughnut charts
- [x] 🔍 **Global Search**: Async customer search with API integration
- [x] ⌨️ **Keyboard Shortcuts**: Ctrl+K for search, Esc for close
- [x] 🔔 **Toast Notifications**: Real-time feedback for user actions
- [x] 📄 **Alembic Migrations**: Versioned database schema migrations

> ✨ More features are continuously being added as the project evolves.

<div align="right">

[![][back-to-top]](#readme-top)

</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     SECTION: Tech Stack
     ═══════════════════════════════════════════════════════════════════════════ -->

## 🛠️ Tech Stack

<div align="center">
  <table>
    <tr>
      <td align="center" width="96">
        <img src="https://cdn.simpleicons.org/python" width="48" height="48" alt="Python" />
        <br>Python 3.9+
      </td>
      <td align="center" width="96">
        <img src="https://cdn.simpleicons.org/flask" width="48" height="48" alt="Flask" />
        <br>Flask 3.1.3
      </td>
      <td align="center" width="96">
        <img src="https://cdn.simpleicons.org/postgresql" width="48" height="48" alt="PostgreSQL" />
        <br>Neon PG
      </td>
      <td align="center" width="96">
        <img src="https://cdn.simpleicons.org/stripe" width="48" height="48" alt="Stripe" />
        <br>Stripe
      </td>
      <td align="center" width="96">
        <img src="https://cdn.simpleicons.org/bootstrap" width="48" height="48" alt="Bootstrap" />
        <br>Bootstrap 5.3
      </td>
      <td align="center" width="96">
        <img src="https://cdn.simpleicons.org/chartdotjs" width="48" height="48" alt="Chart.js" />
        <br>Chart.js 4.4
      </td>
      <td align="center" width="96">
        <img src="https://cdn.simpleicons.org/heroku" width="48" height="48" alt="Heroku" />
        <br>Heroku
      </td>
    </tr>
  </table>
</div>

**Backend:**
- **Framework**: Flask 3.1.3 with application factory pattern
- **ORM**: SQLAlchemy 2.0.36 with custom model mixins
- **Database**: Neon PostgreSQL (cloud) / SQLite (testing)
- **Migrations**: Alembic 1.14.0
- **Authentication**: Authlib 1.6.6 (Google OAuth) + PyJWT 2.10.1 (Neon Auth)
- **Payments**: Stripe 11.4.1 (subscriptions, checkout, webhooks)
- **WSGI Server**: Gunicorn 23.0.0

**Frontend:**
- **Framework**: Bootstrap 5.3 with custom CSS design system
- **Charts**: Chart.js 4.4.0 for data visualization
- **Icons**: Lucide Icons (CDN, client-side rendering)
- **Typography**: DM Sans + Source Sans 3 + JetBrains Mono (Google Fonts)
- **JavaScript**: Vanilla ES6+ (no build tools required)

**DevOps:**
- **Deployment**: Heroku with Procfile (Gunicorn)
- **Database**: Neon PostgreSQL (serverless, auto-scaling)
- **Code Quality**: Black (formatting), isort (imports), flake8 (linting), mypy (types)
- **Testing**: pytest + pytest-cov (70% minimum threshold)

> [!TIP]
> Each technology was selected for production readiness, simplicity, and Flask ecosystem compatibility. No frontend build step is required — static assets are served directly by Flask.

<div align="right">

[![][back-to-top]](#readme-top)

</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     SECTION: Architecture
     ═══════════════════════════════════════════════════════════════════════════ -->

## 🏗️ Architecture

> [!TIP]
> The architecture follows Flask best practices with a clear separation of concerns: views handle HTTP, services encapsulate business logic, and models manage data access with automatic tenant scoping.

<table>
<tbody>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>High-Level Architecture</strong></summary><br>

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                             │
│     Bootstrap 5.3 · Lucide Icons · Chart.js 4.4 · Vanilla ES6+     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────┴────────────────────────────────────┐
│                     Flask Application (WSGI)                         │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                     Middleware Layer                            │  │
│  │   Tenant Context Resolution · Security Headers · CSRF Token    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                  Blueprints (Views Layer)                       │  │
│  │   main · auth · technician · administrator · billing ·         │  │
│  │   onboarding                                                    │  │
│  │   Each registered at /prefix and /org/<slug>/prefix             │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Services Layer                               │  │
│  │   AuthService · NeonAuthService · OAuthService ·                │  │
│  │   CustomerService · JobService · BillingService ·               │  │
│  │   TenantService · StripeService                                 │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                     Models Layer (ORM)                          │  │
│  │   User · Tenant · TenantMembership · Customer · Job ·          │  │
│  │   Service · Part · Inventory · Subscription                     │  │
│  │   ──────────────────────────────────────────                    │  │
│  │   Mixins: BaseModelMixin · TenantScopedMixin · TimestampMixin  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
          ┌──────┴──────┐ ┌─────┴─────┐ ┌───────┴───────┐
          │   Neon       │ │  Google   │ │    Stripe     │
          │  PostgreSQL  │ │  OAuth    │ │   Payments    │
          └─────────────┘ └───────────┘ └───────────────┘
```

</details>
</td>
</tr>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Multi-Tenant Data Flow</strong></summary><br>

```
┌──────────┐     ┌──────────────┐     ┌───────────────────┐     ┌──────────┐
│  Request  │────>│  Tenant      │────>│  Blueprint View   │────>│  Service │
│           │     │  Middleware   │     │  (@login_required │     │  Layer   │
│  /org/    │     │              │     │   @tenant_required│     │          │
│  <slug>/  │     │  Resolves:   │     │   @permission_    │     │  Fresh   │
│  tech/    │     │  URL slug    │     │    required)      │     │  instance│
│  jobs     │     │  Session     │     │                   │     │  per     │
│           │     │  X-Tenant-ID │     │                   │     │  request │
└──────────┘     │              │     └───────────────────┘     └────┬─────┘
                  │  Sets:       │                                    │
                  │  g.current_  │     ┌───────────────────┐         │
                  │  tenant_id   │     │  TenantScoped     │<────────┘
                  └──────────────┘     │  Mixin            │
                                       │                   │
                                       │  Auto-filters     │
                                       │  all queries by   │
                                       │  g.current_       │
                                       │  tenant_id        │
                                       └────────┬──────────┘
                                                │
                                       ┌────────┴──────────┐
                                       │  Neon PostgreSQL   │
                                       │  (shared schema)   │
                                       └───────────────────┘
```

</details>
</td>
</tr>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Authentication Flow</strong></summary><br>

```
┌─────────────────────────────────────────────────────────────┐
│                   Authentication Methods                      │
├─────────────────┬──────────────────┬────────────────────────┤
│                 │                  │                          │
│  ① Password     │  ② Google OAuth  │  ③ Neon Auth JWT        │
│  /login POST    │  /auth/google    │  /auth/callback         │
│                 │       │          │       │                  │
│  AuthService.   │  Authlib         │  NeonAuthService.       │
│  authenticate() │  redirect to     │  verify_token()         │
│       │         │  Google → back   │       │                 │
│       │         │  to /auth/       │  User.authenticate_     │
│       │         │  google/callback │  with_jwt()             │
│       │         │       │          │  (auto-creates user)    │
│       ▼         │       ▼          │       ▼                 │
├─────────────────┴──────────────────┴────────────────────────┤
│                                                              │
│  Session Established:                                        │
│  session['logged_in'] = True                                 │
│  session['user_id'] = user.user_id                          │
│  session['current_tenant_id'] = tenant.tenant_id            │
│  session['current_role'] = membership.role                   │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Multiple Tenants?  ──Yes──>  /auth/select-tenant            │
│        │                                                     │
│       No                                                     │
│        │                                                     │
│        ▼                                                     │
│  Redirect based on role:                                     │
│  admin/owner → /administrator/dashboard                      │
│  technician  → /technician/current-jobs                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

</details>
</td>
</tr>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Project Structure</strong></summary><br>

```
automotive-repair-management-system/
├── app/
│   ├── __init__.py              # Application factory (create_app)
│   ├── extensions.py            # Flask-SQLAlchemy initialization
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── base.py              # BaseModelMixin, TenantScopedMixin, TimestampMixin
│   │   ├── user.py              # User model + ROLE_PERMISSIONS dict
│   │   ├── tenant.py            # Tenant (organization) model
│   │   ├── tenant_membership.py # User-Tenant relationship with role
│   │   ├── customer.py          # Customer model (tenant-scoped)
│   │   ├── job.py               # Job, JobService, JobPart models
│   │   ├── service.py           # Service catalog (tenant-scoped)
│   │   ├── part.py              # Parts catalog (tenant-scoped)
│   │   ├── inventory.py         # Inventory + InventoryTransaction
│   │   └── subscription.py      # Stripe subscription model
│   ├── services/                # Business logic layer
│   │   ├── auth_service.py      # Auth + NeonAuthService (JWT/JWKS)
│   │   ├── oauth_service.py     # Google OAuth via Authlib
│   │   ├── job_service.py       # Work order operations
│   │   ├── customer_service.py  # Customer management
│   │   ├── billing_service.py   # Billing & payment logic
│   │   ├── tenant_service.py    # Organization management + catalog seeding
│   │   └── stripe_service.py    # Stripe checkout, subscriptions, webhooks
│   ├── views/                   # Flask blueprints (route handlers)
│   │   ├── main.py              # Public routes, customer CRUD
│   │   ├── auth.py              # OAuth, JWT, tenant selection, org registration
│   │   ├── technician.py        # Technician portal (jobs, services, parts)
│   │   ├── administrator.py     # Admin portal (customers, billing, catalog, team)
│   │   ├── billing.py           # Stripe checkout & webhook handler
│   │   └── onboarding.py        # 4-step onboarding flow
│   ├── middleware/
│   │   └── tenant.py            # Tenant context resolution middleware
│   ├── utils/
│   │   ├── decorators.py        # @login_required, @tenant_required, @permission_required
│   │   ├── security.py          # CSRF, password hashing, input sanitization, SQL injection
│   │   ├── validators.py        # Email, phone, date, cost, quantity validation
│   │   ├── error_handler.py     # Custom exceptions + HTTP error handlers
│   │   └── database.py          # Database exception classes
│   ├── templates/               # Jinja2 templates (see below)
│   └── static/                  # CSS, JS, images (no build step)
├── config/
│   └── base.py                  # BaseConfig, DevelopmentConfig, ProductionConfig, TestingConfig
├── migrations/
│   ├── env.py                   # Alembic environment
│   └── versions/                # 001-003: multi-tenant schema migrations
├── tests/
│   ├── conftest.py              # Fixtures: app, client, authenticated/admin sessions
│   ├── utils.py                 # Mock builders, test helpers
│   ├── unit/                    # Auth, models, security, multi-tenant tests
│   └── integration/             # View/route integration tests
├── docs/deployment/             # Heroku, Neon, Quick Start guides
├── run.py                       # Development server entry point
├── wsgi.py                      # Production WSGI entry point
├── Procfile                     # Heroku: gunicorn wsgi:application
├── requirements.txt             # Python dependencies (pinned versions)
├── pyproject.toml               # Project metadata + tool configs (black, isort, pytest, mypy)
└── pytest.ini                   # Test configuration with markers
```

**Template Structure:**

```
app/templates/
├── base/layout.html             # Main layout (Precision Industrial design)
├── base.html                    # Landing page layout
├── auth/                        # Login, tenant selection, org registration
├── technician/                  # Dashboard, jobs, services, parts (7 templates)
├── administrator/               # Dashboard, customers, billing, catalog, team (12 templates)
├── billing/                     # Plans, checkout success
├── onboarding/                  # Steps 1-4, completion
├── components/                  # Flash messages, pagination, spinner, toasts
└── errors/                      # 404, 403, 500 error pages
```

</details>
</td>
</tr>
</tbody>
</table>

<div align="right">

[![][back-to-top]](#readme-top)

</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     SECTION: Database Schema
     ═══════════════════════════════════════════════════════════════════════════ -->

## 📊 Database Schema

<table>
<tbody>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Entity Relationship Diagram</strong></summary><br>

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│    Tenant     │──1:N──│ TenantMembership │──N:1──│     User     │
│              │       │                  │       │              │
│  tenant_id   │       │  id              │       │  user_id     │
│  name        │       │  user_id (FK)    │       │  username    │
│  slug        │       │  tenant_id (FK)  │       │  email       │
│  business_   │       │  role            │       │  password_   │
│    type      │       │  is_default      │       │    hash      │
│  status      │       │  invited_by (FK) │       │  is_super-   │
│  settings    │       │  status          │       │    admin     │
│  trial_ends_ │       └──────────────────┘       │  is_active   │
│    at        │                                   │  neon_auth_  │
│              │       ┌──────────────────┐       │    user_id   │
│              │──1:1──│  Subscription    │       └──────────────┘
│              │       │  tenant_id (FK)  │
└──────┬───────┘       │  stripe_*_id     │
       │               │  plan · status   │
       │               └──────────────────┘
       │
       ├──1:N──┬────────────────┬───────────────┬───────────────┐
       │       │                │               │               │
┌──────┴──┐ ┌──┴──────┐ ┌──────┴────┐ ┌────────┴──┐ ┌─────────┴──┐
│Customer │ │  Job     │ │ Service   │ │   Part    │ │ Inventory  │
│         │ │          │ │           │ │           │ │            │
│customer_│ │ job_id   │ │service_id │ │ part_id   │ │inventory_id│
│  id     │ │ job_date │ │service_   │ │ part_name │ │ part_id    │
│first_   │ │ customer │ │  name     │ │ cost      │ │ qty_on_hand│
│  name   │ │  (FK)    │ │ cost      │ │ sku       │ │ reorder_   │
│family_  │ │total_cost│ │description│ │description│ │   level    │
│  name   │ │completed │ │ category  │ │ category  │ │ location   │
│email    │ │ paid     │ │est_dur_min│ │ supplier  │ │            │
│phone    │ │assigned_ │ │ is_active │ │ is_active │ │            │
│         │ │  to (FK) │ │           │ │           │ │            │
└─────────┘ └────┬─────┘ └─────┬─────┘ └─────┬─────┘ └──────┬─────┘
                 │             │             │              │
                 │  ┌──────────┴─┐  ┌───────┴──────┐       │
                 ├──│ JobService  │  │  JobPart     │──┤    │
                 │  │ job_id (PK) │  │ job_id (PK)  │  │    │
                 │  │ service_id  │  │ part_id (PK) │  │    │
                 │  │  (PK) · qty │  │ qty          │  │    │
                 │  └─────────────┘  └──────────────┘  │    │
                 │                                      │    │
                 └──────────────────────────────────────┘    │
                                                             │
                                               ┌─────────────┴──┐
                                               │ Inventory      │
                                               │ Transaction    │
                                               │ transaction_id │
                                               │ transaction_   │
                                               │   type         │
                                               │ quantity       │
                                               │ performed_by   │
                                               │ notes          │
                                               └────────────────┘
```

</details>
</td>
</tr>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Table Details — Core Tables</strong></summary><br>

#### `user`
| Column | Type | Constraints |
|--------|------|-------------|
| `user_id` | Integer | PK |
| `username` | String(50) | UNIQUE, NOT NULL, indexed |
| `email` | String(320) | UNIQUE, indexed |
| `password_hash` | String(255) | NOT NULL |
| `is_superadmin` | Boolean | default: false |
| `is_active` | Boolean | default: true |
| `last_login` | DateTime | nullable |
| `role` | String(20) | indexed (legacy field) |
| `neon_auth_user_id` | String(255) | UNIQUE, indexed |
| `created_at` / `updated_at` | DateTime | auto-managed |

#### `tenant`
| Column | Type | Constraints |
|--------|------|-------------|
| `tenant_id` | Integer | PK |
| `name` | String(100) | NOT NULL |
| `slug` | String(100) | UNIQUE, NOT NULL, indexed |
| `business_type` | String(20) | NOT NULL, default: `auto_repair` |
| `email` | String(320) | nullable |
| `phone` | String(20) | nullable |
| `address` | Text | nullable |
| `logo_url` | String(500) | nullable |
| `status` | String(20) | NOT NULL, default: `trial` |
| `settings` | JSON | nullable |
| `trial_ends_at` | DateTime | nullable |
| `created_at` / `updated_at` | DateTime | auto-managed |

Types: `auto_repair` · `parts_seller` · `both` &nbsp; Statuses: `trial` · `active` · `suspended`

#### `tenant_membership`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `user_id` | Integer | FK → user, NOT NULL |
| `tenant_id` | Integer | FK → tenant, NOT NULL |
| `role` | String(20) | NOT NULL, default: `viewer` |
| `is_default` | Boolean | default: false |
| `invited_by` | Integer | FK → user |
| `status` | String(20) | NOT NULL, default: `pending` |
| `created_at` / `updated_at` | DateTime | auto-managed |

UNIQUE: `(user_id, tenant_id)` &nbsp; Roles: `owner` · `admin` · `manager` · `technician` · `parts_clerk` · `viewer`

</details>
</td>
</tr>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Table Details — Business Tables</strong></summary><br>

#### `customer`
| Column | Type | Constraints |
|--------|------|-------------|
| `customer_id` | Integer | PK |
| `tenant_id` | Integer | FK → tenant, indexed |
| `first_name` | String(25) | nullable |
| `family_name` | String(25) | NOT NULL |
| `email` | String(320) | NOT NULL |
| `phone` | String(11) | NOT NULL |

UNIQUE: `(tenant_id, email)`

#### `job`
| Column | Type | Constraints |
|--------|------|-------------|
| `job_id` | Integer | PK |
| `tenant_id` | Integer | FK → tenant, indexed |
| `job_date` | Date | NOT NULL |
| `customer` | Integer | FK → customer (CASCADE), NOT NULL |
| `total_cost` | Numeric(6,2) | nullable |
| `completed` | Boolean | default: false |
| `paid` | Boolean | default: false |
| `assigned_to` | Integer | FK → user |

Computed: `is_overdue` (hybrid), `status_text`, `days_since_job`

#### `service`
| Column | Type | Constraints |
|--------|------|-------------|
| `service_id` | Integer | PK |
| `tenant_id` | Integer | FK → tenant, indexed |
| `service_name` | String(100) | NOT NULL |
| `cost` | Numeric(5,2) | NOT NULL |
| `description` | String(500) | nullable |
| `category` | String(50) | nullable |
| `estimated_duration_minutes` | Integer | nullable |
| `is_active` | Boolean | default: true |

#### `part`
| Column | Type | Constraints |
|--------|------|-------------|
| `part_id` | Integer | PK |
| `tenant_id` | Integer | FK → tenant, indexed |
| `part_name` | String(100) | NOT NULL |
| `cost` | Numeric(5,2) | NOT NULL |
| `sku` | String(50) | nullable |
| `description` | String(500) | nullable |
| `category` | String(50) | nullable |
| `supplier` | String(100) | nullable |
| `is_active` | Boolean | default: true |

UNIQUE: `(tenant_id, sku)`

#### `job_service` (junction)
| Column | Type | Constraints |
|--------|------|-------------|
| `job_id` | Integer | PK, FK → job (CASCADE) |
| `service_id` | Integer | PK, FK → service (CASCADE) |
| `qty` | Integer | NOT NULL, default: 1 |

#### `job_part` (junction)
| Column | Type | Constraints |
|--------|------|-------------|
| `job_id` | Integer | PK, FK → job (CASCADE) |
| `part_id` | Integer | PK, FK → part (CASCADE) |
| `qty` | Integer | NOT NULL, default: 1 |

</details>
</td>
</tr>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Table Details — Inventory & Billing</strong></summary><br>

#### `inventory`
| Column | Type | Constraints |
|--------|------|-------------|
| `inventory_id` | Integer | PK |
| `tenant_id` | Integer | FK → tenant, NOT NULL, indexed |
| `part_id` | Integer | FK → part, NOT NULL |
| `quantity_on_hand` | Integer | NOT NULL, default: 0 |
| `reorder_level` | Integer | NOT NULL, default: 0 |
| `reorder_quantity` | Integer | NOT NULL, default: 0 |
| `location` | String(100) | nullable |
| `created_at` / `updated_at` | DateTime | auto-managed |

#### `inventory_transaction`
| Column | Type | Constraints |
|--------|------|-------------|
| `transaction_id` | Integer | PK |
| `tenant_id` | Integer | FK → tenant, NOT NULL, indexed |
| `inventory_id` | Integer | FK → inventory, NOT NULL |
| `transaction_type` | String(20) | NOT NULL |
| `quantity` | Integer | NOT NULL |
| `reference_id` | Integer | nullable |
| `reference_type` | String(50) | nullable |
| `performed_by` | Integer | FK → user |
| `notes` | Text | nullable |
| `created_at` | DateTime | NOT NULL |

Transaction types: `received` · `sold` · `adjusted` · `returned`

#### `subscription`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `tenant_id` | Integer | FK → tenant, UNIQUE, NOT NULL |
| `stripe_customer_id` | String(255) | nullable |
| `stripe_subscription_id` | String(255) | nullable |
| `plan` | String(20) | NOT NULL, default: `free` |
| `status` | String(20) | NOT NULL, default: `trialing` |
| `current_period_start` / `current_period_end` | DateTime | nullable |
| `trial_ends_at` | DateTime | nullable |
| `created_at` / `updated_at` | DateTime | auto-managed |

Plans: `free` · `starter` · `professional` · `enterprise` &nbsp; Statuses: `trialing` · `active` · `past_due` · `canceled`

</details>
</td>
</tr>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Alembic Migration History</strong></summary><br>

| Version | Description |
|---------|-------------|
| `001` | Create multi-tenant tables (tenant, membership, subscription, inventory, inventory_transaction). Add `tenant_id` and new columns to existing tables. |
| `002` | Backfill default tenant (tenant_id=1) for existing data. |
| `003` | Enforce `NOT NULL` constraints on `tenant_id`. Add unique constraints: `(tenant_id, email)` on customer, `(tenant_id, sku)` on part. |

</details>
</td>
</tr>
</tbody>
</table>

<div align="right">

[![][back-to-top]](#readme-top)

</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     SECTION: Getting Started
     ═══════════════════════════════════════════════════════════════════════════ -->

## 🚀 Getting Started

### Prerequisites

> [!IMPORTANT]
> Ensure you have the following installed:

- Python 3.9+ ([Download](https://www.python.org/downloads/))
- Git ([Download](https://git-scm.com/))
- [Optional] Node.js 18+ (for Neon CLI)
- [Optional] Google Cloud Console account (for OAuth)
- [Optional] Stripe account (for billing)

### Quick Installation

**1. Clone Repository**

```bash
git clone https://github.com/ChanMeng666/automotive-repair-management-system.git
cd automotive-repair-management-system
```

**2. Create Virtual Environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

**3. Install Dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure Environment**

```bash
cp .env.example .env
# Edit .env with your settings (see Environment Variables below)
```

**5. Set Up Neon Database** (Optional — app auto-creates tables in dev mode)

```bash
# Option A: Neon CLI
npm install -g neonctl
neonctl auth
neonctl projects create --name automotive-repair
neonctl connection-string PROJECT_ID
# Copy connection string to DATABASE_URL in .env

# Option B: Neon Console
# Create project at https://console.neon.tech
# Copy connection string from Connection Details
```

**6. Set Up Google OAuth** (Optional for local dev)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID
3. Add redirect URI: `http://localhost:5000/auth/google/callback`
4. Copy Client ID and Secret to `.env`

**7. Run Application**

```bash
python run.py
```

Open [http://localhost:5000](http://localhost:5000)

> [!TIP]
> In development mode, the app auto-creates all database tables on startup. No manual schema setup required.

### Environment Variables

> [!WARNING]
> Never commit `.env` files to version control. Use `.env.example` as a template.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_ENV` | 🔶 | `development` | `development` / `production` |
| `SECRET_KEY` | ✅ (prod) | dev default | Flask session encryption key |
| `DATABASE_URL` | ✅ (prod) | SQLite in-memory | Neon PostgreSQL connection string |
| `DB_SSLMODE` | 🔶 | `require` | SSL mode: `require` / `prefer` / `disable` |
| `GOOGLE_CLIENT_ID` | 🔶 | — | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | 🔶 | — | Google OAuth Client Secret |
| `NEON_AUTH_URL` | 🔶 | — | Neon Auth URL for JWT verification |
| `NEON_AUTH_JWKS_URL` | 🔶 | — | JWKS endpoint URL |
| `STRIPE_API_KEY` | 🔶 | — | Stripe API key for billing |
| `HOST` | 🔶 | `127.0.0.1` | Development server host |
| `PORT` | 🔶 | `5000` | Development server port |
| `LOG_LEVEL` | 🔶 | `INFO` | Logging level |
| `LOG_TO_STDOUT` | 🔶 | `false` | Set `true` for cloud deployments |

> ✅ Required &nbsp; 🔶 Optional

> [!TIP]
> Use `python -c "import secrets; print(secrets.token_hex(32))"` to generate a secure `SECRET_KEY`.

<div align="right">

[![][back-to-top]](#readme-top)

</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     SECTION: Deployment
     ═══════════════════════════════════════════════════════════════════════════ -->

## 🛳 Deployment

> [!IMPORTANT]
> The application is production-ready with Heroku deployment via Gunicorn. Neon PostgreSQL provides a serverless, auto-scaling database.

### Deploy to Heroku

**1. Create Heroku App**

```bash
heroku create your-app-name
```

**2. Configure Environment Variables**

```bash
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set FLASK_ENV=production
heroku config:set LOG_TO_STDOUT=true
heroku config:set DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/db?sslmode=require"
heroku config:set GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
heroku config:set GOOGLE_CLIENT_SECRET="your-client-secret"
```

**3. Deploy**

```bash
git push heroku main
```

**4. Google OAuth for Production**

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Add authorized redirect URI: `https://repairos.chanmeng.org/auth/google/callback`
3. Add authorized JavaScript origin: `https://repairos.chanmeng.org`

### Database Migrations

```bash
# Migrations are managed via Alembic in migrations/versions/
# Current versions: 001 (multi-tenant tables) → 002 (backfill) → 003 (constraints)
```

<div align="right">

[![][back-to-top]](#readme-top)

</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     SECTION: API Reference
     ═══════════════════════════════════════════════════════════════════════════ -->

## 📖 API Reference

> [!TIP]
> All routes require authentication unless marked otherwise. Tenant-scoped routes are also available at `/org/<tenant_slug>/...`.

<table>
<tbody>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Public Routes</strong></summary><br>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page with statistics dashboard |
| GET/POST | `/login` | Login page and handler |
| GET | `/logout` | Logout |
| GET | `/about` | About page |
| GET | `/help` | Help page |
| GET | `/customers` | Customer list |
| GET/POST | `/customers/new` | New customer form / create |
| GET | `/customers/<id>` | Customer detail |
| GET/POST | `/customers/<id>/edit` | Edit customer |
| GET | `/api/search/customers?q=` | Customer search API (JSON) |
| GET | `/api/customers/<id>` | Customer details API (JSON) |

</details>
</td>
</tr>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Authentication Routes (/auth)</strong></summary><br>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/auth/google` | Initiate Google OAuth |
| GET | `/auth/google/callback` | Google OAuth callback |
| GET | `/auth/callback` | Neon Auth JWT callback |
| POST | `/auth/neon-callback` | JS client auth notification |
| GET | `/auth/session` | Current session info (JSON) |
| POST | `/auth/logout` | API logout |
| POST | `/auth/verify-token` | Verify JWT token |
| POST | `/auth/link-account` | Link Neon Auth to local account |
| GET | `/auth/status` | OAuth provider config status |
| GET | `/auth/select-tenant` | Tenant selection page |
| POST | `/auth/switch-tenant` | Switch active tenant |
| GET/POST | `/auth/register-organization` | Register new organization |

</details>
</td>
</tr>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Technician Routes (/technician)</strong></summary><br>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/technician/dashboard` | Technician dashboard |
| GET | `/technician/current-jobs?page=` | Current work orders (paginated) |
| GET | `/technician/jobs/<id>` | Work order detail |
| GET | `/technician/jobs/<id>/modify` | Modify work order |
| POST | `/technician/jobs/<id>/add-service` | Add service to work order |
| POST | `/technician/jobs/<id>/add-part` | Add part to work order |
| POST | `/technician/jobs/<id>/complete` | Mark work order complete |
| GET | `/technician/jobs/new` | New work order form |
| POST | `/technician/jobs` | Create work order |
| GET | `/technician/services` | Service catalog |
| GET | `/technician/parts` | Parts list |
| GET | `/technician/api/services` | All services (JSON) |
| GET | `/technician/api/parts` | All parts (JSON) |
| GET | `/technician/api/jobs/<id>/status` | Work order status (JSON) |

</details>
</td>
</tr>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Administrator Routes (/administrator)</strong></summary><br>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/administrator/dashboard` | Admin dashboard with charts |
| GET | `/administrator/customers?page=` | Customer management (paginated) |
| GET | `/administrator/billing` | Billing management |
| GET | `/administrator/overdue-bills` | Overdue bills |
| GET | `/administrator/pay-bills` | Payment processing |
| POST | `/administrator/customers/<id>/pay` | Pay all customer bills |
| POST | `/administrator/jobs/<id>/pay` | Pay single bill |
| GET | `/administrator/reports` | Reports page |
| GET/POST | `/administrator/settings` | Organization settings |
| GET | `/administrator/team` | Team member management |
| POST | `/administrator/team/invite` | Invite team member |
| GET/POST | `/administrator/services` | Service catalog management |
| GET/POST | `/administrator/parts` | Parts catalog management |
| GET | `/administrator/inventory` | Inventory dashboard |
| POST | `/administrator/inventory/adjust` | Adjust inventory stock |
| GET | `/administrator/subscription` | Subscription management |
| GET | `/administrator/api/dashboard/summary` | Dashboard summary (JSON) |
| GET | `/administrator/api/billing/statistics` | Billing statistics (JSON) |
| GET | `/administrator/api/customers/<id>/billing-summary` | Billing summary (JSON) |
| GET | `/administrator/api/export/customers` | Export customer data (JSON) |

</details>
</td>
</tr>
<tr></tr>
<tr>
<td width="10000">
<details>

<summary>&nbsp;&nbsp;<strong>Billing & Onboarding Routes</strong></summary><br>

**Billing (`/billing`):**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/billing/plans` | Subscription plans |
| POST | `/billing/checkout` | Create Stripe checkout session |
| GET | `/billing/success` | Checkout success page |
| POST | `/billing/portal` | Redirect to Stripe billing portal |
| POST | `/billing/webhook` | Stripe webhook handler (no auth) |

**Onboarding (`/onboarding`):**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/onboarding/step/<num>` | Display onboarding step (1-4) |
| POST | `/onboarding/step/<num>` | Save onboarding step data |
| GET | `/onboarding/complete` | Onboarding completion |

</details>
</td>
</tr>
</tbody>
</table>

<div align="right">

[![][back-to-top]](#readme-top)

</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     SECTION: Development
     ═══════════════════════════════════════════════════════════════════════════ -->

## ⌨️ Development

### Development Scripts

```bash
# Development
python run.py                              # Start dev server (localhost:5000)

# Testing
pytest                                     # Run all tests
pytest --cov=app                           # Run with coverage (70% minimum)
pytest -m unit                             # Run unit tests only
pytest -m integration                      # Run integration tests only
pytest -m security                         # Run security tests only
pytest tests/unit/test_models.py -v        # Single test file
pytest tests/unit/test_auth.py::TestUserModel::test_create_user -v  # Single test

# Code Quality
black --line-length 100 .                  # Format code
isort .                                    # Sort imports
flake8 app/                                # Lint code
mypy app/                                  # Type checking

# Production
gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### Testing

> [!TIP]
> Tests use SQLite in-memory database — no PostgreSQL setup needed.

**Fixtures** (in `tests/conftest.py`):
- `app` — Session-scoped Flask app with `TestingConfig`
- `client` — Function-scoped test client
- `authenticated_session` — Pre-authenticated technician (tenant_id=1)
- `admin_session` — Pre-authenticated admin/owner (tenant_id=1)

**Test Markers:**
- `@pytest.mark.unit` — Unit tests
- `@pytest.mark.integration` — Integration tests
- `@pytest.mark.security` — Security tests
- `@pytest.mark.slow` — Slow-running tests

<div align="right">

[![][back-to-top]](#readme-top)

</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     SECTION: Contributing
     ═══════════════════════════════════════════════════════════════════════════ -->

## 🤝 Contributing

Contributions are welcome! Here's how you can help improve this project:

**1. Fork & Clone:**

```bash
git clone https://github.com/ChanMeng666/automotive-repair-management-system.git
cd automotive-repair-management-system
```

**2. Create Branch:**

```bash
git checkout -b feature/your-feature-name
```

**3. Make Changes:**

- Follow Black formatting (line-length: 100)
- Add tests for new features
- Ensure all tests pass with `pytest`
- Update documentation as needed

**4. Submit PR:**

- Provide a clear description of changes
- Reference related issues
- Ensure CI passes

**Issue Reporting:**
- 🐛 **Bug Reports**: Include reproduction steps and environment details
- 💡 **Feature Requests**: Explain the use case and expected behavior
- 📚 **Documentation**: Help improve our docs

[![][pr-welcome-shield]][pr-welcome-link]

<a href="https://github.com/ChanMeng666/automotive-repair-management-system/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ChanMeng666/automotive-repair-management-system" />
</a>

<div align="right">

[![][back-to-top]](#readme-top)

</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     SECTION: License
     ═══════════════════════════════════════════════════════════════════════════ -->

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed

<!-- ═══════════════════════════════════════════════════════════════════════════
     SECTION: Author
     ═══════════════════════════════════════════════════════════════════════════ -->

## 🙋‍♀️ Author

<div align="center">
  <table>
    <tr>
      <td align="center">
        <a href="https://github.com/ChanMeng666">
          <img src="https://github.com/ChanMeng666.png?size=100" width="100px;" alt="Chan Meng"/>
          <br />
          <sub><b>Chan Meng</b></sub>
        </a>
        <br />
        <small>Creator & Lead Developer</small>
      </td>
    </tr>
  </table>
</div>

- <img src="https://cdn.simpleicons.org/internetexplorer/0078D4" width="16" height="16"> Website: [chanmeng.org](https://chanmeng.org)
- <img src="https://cdn.simpleicons.org/github/181717" width="16" height="16"> GitHub: [@ChanMeng666](https://github.com/ChanMeng666)
- <img src="https://cdn.simpleicons.org/linkedin/0A66C2" width="16" height="16"> LinkedIn: [chanmeng666](https://www.linkedin.com/in/chanmeng666/)

---

<div align="center">

**Built with Flask, SQLAlchemy, Neon PostgreSQL, Google OAuth, Stripe, and Bootstrap**

[Report Bug][github-issues-link] · [Request Feature][github-issues-link]

<br/>

<img src="https://img.shields.io/github/stars/ChanMeng666/automotive-repair-management-system?style=social" alt="GitHub stars">
<img src="https://img.shields.io/github/forks/ChanMeng666/automotive-repair-management-system?style=social" alt="GitHub forks">

</div>

---

<!-- ═══════════════════════════════════════════════════════════════════════════
     LINK DEFINITIONS
     ═══════════════════════════════════════════════════════════════════════════ -->

[back-to-top]: https://img.shields.io/badge/-BACK_TO_TOP-151515?style=flat-square

<!-- Project Links -->
[project-link]: https://repairos.chanmeng.org
[github-issues-link]: https://github.com/ChanMeng666/automotive-repair-management-system/issues
[pr-welcome-link]: https://github.com/ChanMeng666/automotive-repair-management-system/pulls
[license-link]: ./LICENSE

<!-- External Links -->
[python-link]: https://python.org
[flask-link]: https://flask.palletsprojects.com
[sqlalchemy-link]: https://www.sqlalchemy.org
[postgresql-link]: https://neon.tech
[stripe-link]: https://stripe.com
[heroku-link]: https://heroku.com
[bootstrap-link]: https://getbootstrap.com

<!-- Shield Badges -->
[python-shield]: https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white
[flask-shield]: https://img.shields.io/badge/Flask-3.1.3-000000?style=for-the-badge&logo=flask&logoColor=white
[sqlalchemy-shield]: https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white
[postgresql-shield]: https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql&logoColor=white
[stripe-shield]: https://img.shields.io/badge/Stripe-Billing-635BFF?style=for-the-badge&logo=stripe&logoColor=white
[heroku-shield]: https://img.shields.io/badge/Heroku-Deployed-430098?style=for-the-badge&logo=heroku&logoColor=white
[bootstrap-shield]: https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white
[license-shield]: https://img.shields.io/badge/License-MIT-green?style=for-the-badge
[pr-welcome-shield]: https://img.shields.io/badge/🤝_PRs_welcome-%E2%86%92-ffcb47?labelColor=black&style=for-the-badge
[demo-shield-badge]: https://img.shields.io/badge/LIVE%20DEMO-ONLINE-55b467?labelColor=black&logo=heroku&style=for-the-badge

<!-- Social Share Links -->
[share-x-link]: https://x.com/intent/tweet?hashtags=flask,saas,opensource&text=Check%20out%20this%20multi-tenant%20automotive%20repair%20management%20platform&url=https%3A%2F%2Fgithub.com%2FChanMeng666%2Fautomotive-repair-management-system
[share-telegram-link]: https://t.me/share/url?text=Multi-tenant%20automotive%20repair%20management%20SaaS%20platform&url=https%3A%2F%2Fgithub.com%2FChanMeng666%2Fautomotive-repair-management-system
[share-reddit-link]: https://www.reddit.com/submit?title=Multi-Tenant%20Automotive%20Repair%20Management%20Platform&url=https%3A%2F%2Fgithub.com%2FChanMeng666%2Fautomotive-repair-management-system
[share-linkedin-link]: https://linkedin.com/sharing/share-offsite/?url=https://github.com/ChanMeng666/automotive-repair-management-system

[share-x-shield]: https://img.shields.io/badge/-share%20on%20x-black?labelColor=black&logo=x&logoColor=white&style=flat-square
[share-telegram-shield]: https://img.shields.io/badge/-share%20on%20telegram-black?labelColor=black&logo=telegram&logoColor=white&style=flat-square
[share-reddit-shield]: https://img.shields.io/badge/-share%20on%20reddit-black?labelColor=black&logo=reddit&logoColor=white&style=flat-square
[share-linkedin-shield]: https://img.shields.io/badge/-share%20on%20linkedin-black?labelColor=black&logo=linkedin&logoColor=white&style=flat-square
"# knb-crm" 
