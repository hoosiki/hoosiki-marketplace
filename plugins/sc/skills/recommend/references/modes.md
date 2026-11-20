# /sc:recommend Modes

Figures here are rough planning guides, not measurements.

## Step 3: Project Context Detection System

### Project Type Detection Algorithm

```yaml
project_detection:
  file_system_analysis:
    react_project:
      indicators: ["package.json with react", "src/App.jsx", "public/", "node_modules/react"]
      detection_commands:
        primary: ["/sc:build --feature --react", "/sc:test --coverage --e2e --play"]
        personas: ["--persona-frontend", "--persona-qa"]
        mcp: ["--c7", "--play"]

    vue_project:
      indicators: ["package.json with vue", "src/App.vue", "vue.config.js"]
      detection_commands:
        primary: ["/sc:build --feature", "/sc:analyze --code --c7"]
        personas: ["--persona-frontend"]
        mcp: ["--c7"]

    node_api_project:
      indicators: ["package.json with express", "server.js", "routes/", "controllers/"]
      detection_commands:
        primary: ["/sc:design --api --ddd --seq", "/sc:build --feature --tdd"]
        personas: ["--persona-backend", "--persona-security"]
        mcp: ["--seq", "--c7"]

    python_project:
      indicators: ["requirements.txt", "setup.py", "src/", "main.py", "Dockerfile"]
      detection_commands:
        primary: ["/sc:analyze --code --seq", "/sc:design --seq --ultrathink"]
        personas: ["--persona-analyzer", "--persona-architect"]
        mcp: ["--seq"]

    database_project:
      indicators: ["schema.sql", "migrations/", "models/", "prisma.schema"]
      detection_commands:
        primary: ["/sc:workflow \"database migration\" --validate", "/sc:analyze --security --seq"]
        personas: ["--persona-backend", "--persona-security"]
        mcp: ["--seq"]

  project_size_estimation:
    small_project:
      file_count: "<50 files"
      complexity: "simple"
      recommended_approach: "direct implementation"

    medium_project:
      file_count: "50-200 files"
      complexity: "moderate"
      recommended_approach: "plan -> analyze -> implement"

    large_project:
      file_count: ">200 files"
      complexity: "complex"
      recommended_approach: "comprehensive analysis -> design -> implement"
```

### Context-Aware Examples

```bash
/sc:recommend "I need to add a new feature"

🎯 Project Analysis: React project - Feature development
📁 Project Context: React application detected (15+ components)
🎭 Persona: --persona-frontend + --persona-qa

✅ Context-Aware Recommendations:
1. /sc:build --feature --react --persona-frontend
   "New component compatible with existing design system"

2. /sc:test --coverage --e2e --play --persona-qa
   "Create tests for new feature"

3. /sc:analyze --code --c7 --persona-frontend
   "React best practices check"

💡 Project-Specific Flags:
--storybook-integration (if Storybook exists)
--component-library (if it's a component library)
--design-system (integration with existing design system)
```

```bash
/sc:recommend "I need to do a security audit"

🎯 Project Analysis: Node.js API - Security audit
📁 Project Context: Express API detected (JWT auth exists)
🎭 Persona: --persona-security + --persona-backend

✅ Context-Aware Recommendations:
1. /sc:analyze --focus security --owasp --deps --strict --persona-security
   "OWASP Top 10 and dependency security scan"

2. /sc:analyze --security --seq --persona-security
   "JWT and authentication pattern analysis"

3. /sc:improve --security --harden --persona-backend
   "Security hardening and production configs"

💡 Project-Specific Flags:
--jwt-validation (JWT token validation)
--rate-limiting (API rate limiting)
--audit-logging (audit logging setup)
```

## Step 4: Real-Time Streaming Mode

### Continuous Recommendation System

```yaml
streaming_mode:
  activation:
    command: "/sc:recommend --stream [project description]"
    purpose: "Continuous recommendation throughout project"

  flow_tracking:
    phase_1: Analysis & Planning
      commands: ["/sc:analyze", "/sc:design"]
      next_phase_trigger: "analysis_complete"

    phase_2: Implementation
      commands: ["/sc:build", "/sc:implement"]
      next_phase_trigger: "implementation_complete"

    phase_3: Testing & Validation
      commands: ["/sc:test", "/sc:analyze"]
      next_phase_trigger: "testing_complete"

    phase_4: Deployment & Monitoring
      commands: ["/sc:build", "/sc:improve"]
      project_complete: true
```

### Streaming Example

```bash
/sc:recommend --stream "I'm building a new e-commerce site"

🚀 STREAMING MODE ACTIVE
📊 Project: E-commerce website
⏱️ Estimated Time: 3-6 weeks

--- PHASE 1: ANALYSIS & PLANNING ---
✅ Current: /sc:analyze --seq --c7 --persona-architect
   "E-commerce architecture and technology selection"

🔄 Next Steps (when completed):
1. /sc:design --api --ddd --seq --ultrathink --persona-architect
2. /sc:build --feature --react --persona-frontend

--- STREAM CONTINUING ---
```

## Step 5: Alternative Recommendation Engine

### Multiple Option Presentation

```yaml
alternative_engine:
  structure:
    primary_recommendation: "Most suitable option"
    alternatives: "2-3 different approaches"
    comparison_matrix: "Advantage/disadvantage analysis"
    community_preference: "Popularity rate"

  categories:
    technology_alternatives:
      frontend: ["React", "Vue", "Angular", "Svelte"]
      backend: ["Node.js", "Python", "Java", "Go"]
      database: ["PostgreSQL", "MongoDB", "MySQL", "Redis"]

    approach_alternatives:
      development: ["TDD", "BDD", "Agile", "Waterfall"]
      deployment: ["Docker", "Kubernetes", "Serverless", "Traditional"]
      testing: ["Unit", "Integration", "E2E", "Performance"]
```

### Alternative Example

```bash
/sc:recommend --alternatives "new blog site"

🎯 PROJECT ANALYSIS: Blog site development

⭐ BEST RECOMMENDATION:
/sc:build --feature --nextjs --persona-frontend
   "Modern, SEO-friendly blog with Next.js"

🔧 ALTERNATIVES:
1. /sc:build --feature --react --static --persona-frontend
   ✅ Advantage: Simpler learning curve
   ❌ Disadvantage: Less SEO optimization

2. /sc:build --feature --vue --nuxt --persona-frontend
   ✅ Advantage: Great developer experience
   ❌ Disadvantage: Smaller community

3. /sc:build --feature --gatsby --static --persona-frontend
   ✅ Advantage: Excellent performance and SEO
   ❌ Disadvantage: More complex configuration

📊 COMPARISON TABLE:
| Technology | Speed | SEO | Learning | Community |
|-----------|-------|-----|----------|-----------|
| Next.js | ⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| React | ⚡⚡ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Vue/Nuxt | ⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Gatsby | ⚡⚡⚡ | ⭐⭐⭐ | ⭐ | ⭐⭐ |

```

## Step 6: Time and Budget Estimation System

### Intelligent Estimation Algorithm

```yaml
estimation_engine:
  complexity_factors:
    project_type:
      simple_component: 1-3 days
      feature_development: 1-2 weeks
      microservice: 2-4 weeks
      full_application: 1-3 months
      enterprise_system: 3-6 months

    experience_multiplier:
      beginner: 2.0x
      intermediate: 1.5x
      expert: 1.0x
      senior: 0.8x

    scope_factors:
      small_scope: 1.0x
      medium_scope: 1.5x
      large_scope: 2.5x
      enterprise_scope: 4.0x

  time_estimates:
    ml_projects:
      data_collection: 20-30% of total time
      preprocessing: 15-25% of total time
      model_training: 10-20% of total time
      evaluation: 10-15% of total time
      deployment: 15-25% of total time

    web_projects:
      design: 15-25% of total time
      frontend: 30-40% of total time
      backend: 25-35% of total time
      testing: 10-20% of total time
      deployment: 5-15% of total time
```

### Estimation Examples

```bash
/sc:recommend "I'm developing a classification model" --estimate

🎯 PROJECT ANALYSIS: Classification model development
📊 Estimation Mode: Active

⏱️ TIME ESTIMATE:
- Total Time: 2-4 weeks
- Data Collection: 4-7 days (20%)
- Preprocessing: 3-5 days (15%)
- Model Training: 2-4 days (10%)
- Evaluation: 2-3 days (10%)
- Deployment: 3-5 days (15%)
- Buffer: 4-7 days (30%)

💰 BUDGET ESTIMATE:
- Development Time: 80-120 hours
- Experience Level: Intermediate (1.5x multiplier)
- Total Effort: 120-180 hours

🎯 CRITICAL FACTORS:
- Data quality and quantity: High impact
- Model complexity: Medium impact
- Deployment requirements: Medium impact

⚠️ RISK ASSESSMENT:
- Data cleaning difficulty: Medium risk
- Model performance: Medium risk
- Model drift: Low risk

🚀 QUICK START: MVP within 1 week
```

```bash
/sc:recommend "corporate website" --estimate

🎯 PROJECT ANALYSIS: Corporate website
📊 Estimation Mode: Active

⏱️ TIME ESTIMATE:
- Total Time: 4-8 weeks
- Design and UX: 1-2 weeks (25%)
- Frontend Development: 2-3 weeks (40%)
- Backend and CMS: 1-2 weeks (25%)
- Testing and Optimization: 0.5-1 week (10%)

💰 BUDGET ESTIMATE:
- Development Time: 160-320 hours
- Team Size: 2-3 people
- Total Project Engineering: 320-960 hours

🎯 FEATURE SCOPE:
- Homepage and services: Required
- About and contact: Required
- Blog/news: Optional (+1 week)
- Admin panel: Optional (+1-2 weeks)
- Multi-language: Optional (+1 week)

📱 DEVICE SUPPORT:
- Responsive design: Included
- Mobile app: Additional 4-8 weeks
- PWA: Additional 1-2 weeks

⚠️ PROJECT RISKS:
- Content management needs: Medium risk
- SEO requirements: Low risk
- Browser compatibility: Low risk
```

## Step 7: Smart Flag Recommendation System

### Context-Based Flag Recommendations

```yaml
smart_flag_engine:
  context_detection:
    project_size:
      small: "--quick --simple --no-validation"
      medium: "--plan --validate --profile"
      large: "--plan --validate --seq --ultrathink"

    security_requirements:
      basic: "--basic-security"
      standard: "--security --validate"
      enterprise: "--security --owasp --strict --audit"

    performance_requirements:
      low_traffic: "--basic-optimization"
      medium_traffic: "--optimize --profile"
      high_traffic: "--optimize --profile --monitoring --benchmark"

    learning_mode:
      beginner: "--tutorial --examples --step-by-step"
      intermediate: "--guided --examples"
      expert: "--advanced --no-explanations"

  intelligent_suggestions:
    based_on_history:
      if_previous_errors: "--validate --dry-run --backup"
      if_security_issues: "--security --scan --strict"
      if_performance_issues: "--profile --optimize --monitor"
      if_large_refactor: "--plan --backup --validate"

    based_on_project_type:
      ml_project: "--data-validation --model-monitoring"
      api_project: "--security --rate-limiting --monitoring"
      frontend_project: "--accessibility --responsive --performance"
      mobile_project: "--offline --sync --battery-optimized"
```

### Smart Flag Examples

```bash
/sc:recommend "performance improvement"

🎯 PROJECT ANALYSIS: Performance optimization
🧠 SMART FLAG RECOMMENDATIONS:

📊 BASED ON HISTORY:
- Previous errors encountered: --validate --backup
- Previous security issues: --security --scan
- Large refactoring history: --plan --dry-run

🎯 PROJECT CONTEXT:
- Large project (>200 files): --seq --ultrathink
- Production environment: --validate --monitoring
- High traffic: --benchmark --profile

💡 RECOMMENDED COMMAND:
/sc:improve --performance --optimize --profile --monitoring --validate

🔧 ADDITIONAL FLAG OPTIONS:
--memory-optimization (if RAM usage is high)
--database-optimization (if DB is slow)
--cdn-integration (if static resources are many)
```

```bash
/sc:recommend "my first React component"

🎯 PROJECT ANALYSIS: React component development - Beginner
🧠 SMART FLAG RECOMMENDATIONS:

📚 LEARNING MODE:
- Beginner detected: --tutorial --examples --step-by-step
- Component development: --design-system

🎯 PROJECT CONTEXT:
- React project: --component-library --storybook
- Accessibility required: --a11y --wcag

💡 RECOMMENDED COMMAND:
/sc:build --feature --react --tutorial --examples --persona-frontend

🔧 ADDITIONAL LEARNING FLAGS:
--guided-development (step-by-step guidance)
--best-practices (React best practices)
--error-handling (error handling examples)
```

## Step 8: Community Patterns and Final Integration

### Community Data-Based Recommendations

```yaml
community_patterns:
  successful_workflows:
    web_development:
      most_successful_flow:
        - "/sc:analyze --code --c7"
        - "/sc:design --api --seq"
        - "/sc:build --feature --tdd"
        - "/sc:test --coverage --e2e --play"

    ml_development:
      most_successful_flow:
        - "/sc:analyze --seq --c7 --persona-mentor"
        - "/sc:design --seq --ultrathink --persona-architect"
        - "/sc:build --feature --tdd --persona-frontend"
        - "/sc:improve --performance --iterate"

  popular_command_combinations:
    security_focused:
      - "/sc:analyze --focus security --owasp"
      - "/sc:analyze --security --seq"
      - "/sc:improve --security --harden"

    performance_optimization:
      - "/sc:analyze --performance --play --profile"
      - "/sc:improve --performance --iterate"
      - "/sc:test --coverage --benchmark"
```

### Final Command Integration

```yaml
recommend_command_implementation:
  command_structure: "/sc:recommend [query] --options [flags]"

  available_options:
    --estimate: "Includes time and budget estimation"
    --alternatives: "Provides multiple solution recommendations"
    --stream: "Continuous project tracking mode"
    --community: "Includes common workflow patterns (illustrative, not measured)"
    --language [<code>|auto]: "Language setting"
    --expertise [beginner|intermediate|expert]: "Level setting"

  response_format:
    analysis_section:
      - 🎯 Project analysis
      - 🌍 Request language
      - 📊 Level determination
      - 🎭 Persona recommendation
      - 📁 Project context

    recommendations_section:
      - ✅ Main recommendations (3 commands)
      - 💡 Additional recommendations (optional)
      - 🔧 Smart flag recommendations
      - 🚀 Quick start options

    enhanced_section:
      - ⏱️ Time/budget estimation (with --estimate)
      - 🔧 Alternative options (with --alternatives)
      - 👥 Common workflow patterns (with --community)
      - 🔄 Continuous flow (with --stream)
```

### Comprehensive Final Example

```bash
/sc:recommend "I'm building an e-commerce site" --estimate --alternatives --community

🎯 COMPREHENSIVE ANALYSIS
==========================

📊 Project Analysis: E-commerce website development
🌍 Language: Turkish detected
📁 Project Context: New project (no existing project)
🎭 Persona: --persona-architect + --persona-frontend + --persona-security
🔍 Category: Web development + E-commerce + Security-focused

✅ BEST RECOMMENDATIONS
=================

1. 🏗️ PLANNING AND DESIGN
   /sc:design --api --ddd --seq --ultrathink --persona-architect
   "E-commerce domain architecture and system design"

2. 🎨 FRONTEND DEVELOPMENT
   /sc:build --feature --nextjs --persona-frontend
   "Modern, SEO-friendly e-commerce frontend"

3. 🔒 SECURITY AND BACKEND
   /sc:build --feature --tdd --persona-security
   "Secure payment system and user management"

🔧 SMART FLAG RECOMMENDATIONS
======================

📚 Learning mode: --tutorial --examples (if you're just starting)
🚀 Quick start: --quick-start --template (e-commerce template)
🔒 Security-focused: --security --owasp --strict (for payment transactions)
⚡ Performance: --optimize --monitoring --cdn (for high traffic)

🔧 ALTERNATIVE TECHNOLOGIES
==========================

⭐ BEST: Next.js + Stripe + PostgreSQL
   ✅ Advantage: Modern stack, great SEO, scalable

🥈 SECOND: Vue.js + Shopify API + Headless CMS
   ✅ Advantage: Faster development, good DX

🥉 THIRD: React + Custom Backend + MongoDB
   ✅ Advantage: Maximum flexibility, full control

⏱️ TIME AND BUDGET ESTIMATE
========================

📅 Project Duration: 6-12 weeks
- Planning & Design: 1-2 weeks
- Frontend Development: 2-4 weeks
- Backend & Payment: 2-3 weeks
- Testing & Security: 1-2 weeks
- Deployment & Launch: 0.5-1 week

💰 Budget Estimate:
- Solo Developer: 240-480 hours
- Small Team (2-3 people): 480-1440 hours
- Enterprise Team: 1440-2880 hours

👥 COMMUNITY DATA
==================

🏆 Most Successful Flow:
/sc:analyze → /sc:design → /sc:build → /sc:test
Success Rate: 87% (from 2,847 projects)

📈 Popular Features:
- User authentication: 94% of projects have it
- Payment integration: 89% of projects have it
- Admin panel: 76% of projects have it
- Inventory management: 68% of projects have it

⚠️ COMMON RISKS:
- Payment security issues: 32% of projects experienced
- Performance scaling: 28% of projects had issues
- Tax calculation complexity: 45% of projects struggled

🚀 ADDITIONAL SUPER RECOMMENDATIONS
===================

💡 Premium Features (+2-4 weeks):
- Multi-vendor marketplace
- Advanced analytics dashboard
- Mobile app (React Native)
- AI-powered recommendations

🔒 Enterprise Security (+1-2 weeks):
- SOC 2 compliance
- Advanced fraud detection
- PCI DSS certification
- Security audit package

📱 Omnichannel Support (+2-3 weeks):
- PWA capabilities
- Mobile-first design
- Social media integration
- Progressive web app

🔄 STREAMING MODE CAN BE ACTIVATED
===================================

To receive continuous recommendations throughout the project:
/sc:recommend --stream "track my e-commerce project"

You'll receive automatic recommendations at each stage! 🚀
```
