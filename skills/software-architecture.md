---
name: software-architecture
description: "Guide for quality focused software architecture. Use when designing, analyzing, or refactoring any part of the system."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Software Architecture Development Skill

This skill provides guidance for quality focused software development and architecture. It is based on Clean Architecture and Domain Driven Design principles.

## Code Style Rules

### General Principles

- **Early return pattern**: Always use early returns when possible, over nested conditions for better readability
- Avoid code duplication through creation of reusable functions and modules
- Decompose long (more than 80 lines of code) components and functions into multiple smaller components and functions.
- Use modern language features and idioms when appropriate.

### Best Practices

#### Library-First Approach

- **ALWAYS search for existing solutions before writing custom code**
  - Check package managers (pip/npm/cargo, etc.) for existing libraries that solve the problem
  - Evaluate existing services solutions
- Use well-tested libraries instead of writing your own complex utils or helpers.
- **When custom code IS justified:**
  - Specific business logic unique to the domain
  - Performance-critical paths
  - Security-sensitive code requiring full control

#### Architecture and Design

- **Clean Architecture & DDD Principles:**
  - Follow domain-driven design and ubiquitous language
  - Separate domain entities from infrastructure concerns
  - Keep business logic independent of frameworks
  - Define use cases clearly and keep them isolated
- **Naming Conventions:**
  - **AVOID** generic names: `utils`, `helpers`, `common`, `shared`
  - **USE** domain-specific names that reflect their purpose
  - Follow bounded context naming patterns
- **Separation of Concerns:**
  - Do NOT mix business logic with UI or presentation components
  - Keep database queries out of core domain logic and presentation layers
  - Maintain clear boundaries between contexts

#### Anti-Patterns to Avoid

- Mixing business logic with presentation or infrastructure code
- Database queries directly in route handlers or UI controllers
- Lack of clear separation of concerns
- `utils` modules with dozens of unrelated functions

#### Code Quality

- Proper error handling with typed catch blocks and clear error messages
- Break down complex logic into smaller, reusable functions
- Avoid deep nesting (max 3 levels)
- Keep functions focused and under 50 lines when possible
- Keep files focused and under 200 lines of code when possible

## When to Use
Use when designing new features, reviewing existing code structure, or making decisions about system component boundaries and architecture.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Do not treat the output as a substitute for environment-specific validation, testing, or expert review.
- Stop and ask for clarification if required inputs, permissions, safety boundaries, or success criteria are missing.
