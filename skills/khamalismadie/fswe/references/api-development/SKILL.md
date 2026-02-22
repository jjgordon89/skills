# API Development

## Clean Controller Architecture

```typescript
// routes/user.ts
import { Router, Request, Response, NextFunction } from 'express'
import { UserService } from '../services/user.service'
import { validateRequest } from '../middleware/validation'

const router = Router()
const userService = new UserService()

router.get('/users', async (req, res, next) => {
  try {
    const users = await userService.findAll(req.query)
    res.json(users)
  } catch (err) {
    next(err)
  }
})

router.post('/users', 
  validateRequest(createUserSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const user = await userService.create(req.body)
      res.status(201).json(user)
    } catch (err) {
      next(err)
    }
  }
)
```

## Error Standardization

```typescript
// Standard error response
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      { "field": "email", "message": "Must be valid email" }
    ]
  }
}
```

## Checklist

- [ ] Use middleware for validation
- [ ] Standardize error responses
- [ ] Add request logging
- [ ] Implement rate limiting
- [ ] Document with OpenAPI/Swagger
- [ ] Add authentication/authorization
