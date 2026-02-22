# System Design Fundamentals

## Overview
Monolith vs Microservices, service boundaries, API contracts, dan scalability patterns.

## Monolith vs Microservices

### When to Use Monolith
- Team size < 10 engineers
- Early startup/MVP phase
- Tightly coupled features
- Simple domain

### When to Use Microservices
- Team size > 20 engineers
- Multiple independent products
- Different scaling requirements
- Polyglot needs

## Service Boundaries

```
┌─────────────────────────────────────────┐
│              User Service               │
│  - Auth, Profile, Preferences          │
└─────────────────────────────────────────┘
          ↕ REST/gRPC
┌─────────────────────────────────────────┐
│            Order Service                │
│  - Cart, Checkout, History              │
└─────────────────────────────────────────┘
          ↕ Event Bus
┌─────────────────────────────────────────┐
│           Notification Service         │
│  - Email, Push, SMS                    │
└─────────────────────────────────────────┘
```

## Checklist

- [ ] Define bounded contexts
- [ ] Map data ownership
- [ ] Choose communication style (sync/async)
- [ ] Plan for failure scenarios
- [ ] Define SLAs
- [ ] Document API contracts

## Tradeoffs

| Aspect | Monolith | Microservices |
|--------|----------|---------------|
| Deployment | Simple | Complex |
| Scaling | Limited | Infinite |
| Debugging | Easy | Hard |
| Team Autonomy | Low | High |
| Data Consistency | Easy | Eventual |
