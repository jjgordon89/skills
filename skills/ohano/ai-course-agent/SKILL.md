---
name: ai-course-agent
description: Auto-generates AI education courses from natural language requests in Chinese. Detects patterns like "帮我生成6年级数学分数乘除法的课程" and calls Edustem API to create and return a course link.
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": [] },
        "env":
          [
            {
              "key": "EDUSTEM_USERNAME",
              "description": "Edustem API username (email)",
              "required": true,
              "secret": true
            },
            {
              "key": "EDUSTEM_PASSWORD",
              "description": "Edustem API password",
              "required": true,
              "secret": true
            }
          ]
      }
  }
---

# AI Course Agent

OpenClaw Skill for auto-generating AI education courses. Detects natural language course generation requests and calls the Edustem API to create ready-to-use course content.

## Quick Start

```typescript
import { isCourseLessonRequest, processUserMessage } from 'ai-course-agent';

// When user sends a message:
if (isCourseLessonRequest(userInput)) {
  const response = await processUserMessage(userInput);
  // Returns: "✅ 成功为6年级数学《分数乘除法》生成课程！\n\n📚 课程链接: https://..."
}
```

## Configuration

Set environment variables before use:

```bash
export EDUSTEM_USERNAME="your-email@example.com"
export EDUSTEM_PASSWORD="your-password"
```

## Supported Input Patterns

```
帮我生成6年级数学分数乘除法的课程
帮我创建一个七年级语文从百草园到三味书屋的课程
帮我制作9年级英语日常会话的课程
生成8年级科学地球和宇宙的课程
```

Supports both Arabic (6年级) and Chinese (六年级) numerals for grade levels.

## Supported Subjects

数学 · 语文 · 英语 · 科学 · 历史 · 地理 · 物理 · 化学 · 生物

## Output Format

```
✅ 成功为6年级数学《分数乘除法》生成课程！

📚 课程链接: https://your-api-host/ai-lesson/{lesson_ref}
```

## API Flow

1. `login()` — Authenticate and get JWT token
2. `createLessonPlan()` — Create lesson plan with metadata
3. `acceptLessonPlan()` — Confirm and trigger course generation
4. Return course URL

## Exports

```typescript
// Main integration functions
isCourseLessonRequest(message: string): boolean
processUserMessage(userInput: string): Promise<string>

// Core functions
generateCourse(request: CourseRequest): Promise<GeneratedCourseResponse>
parseCourseRequest(userInput: string): CourseRequest | null

// Edustem API (lower level)
login(username, password): Promise<string>
createLessonPlan(token, payload): Promise<CreateLessonPlanResponse>
acceptLessonPlan(token, lessonRef): Promise<AcceptLessonPlanResponse>
generateLessonUrl(lessonRef): string
```

## Tech Stack

TypeScript · Node.js · axios · form-data
