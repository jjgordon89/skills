/**
 * Planning and Reflection
 *
 * Generates execution plans and assesses progress after actions.
 */
// ============================================================================
// Plan Generation
// ============================================================================
const PLAN_GENERATION_PROMPT = `Given the user's goal, create a structured execution plan.

Goal: {goal}

Create a plan with:
1. Clear subtasks (2-7 steps, max {maxSteps})
2. Dependencies between steps (which steps must complete before others)
3. Success criteria for each step
4. Estimated complexity (low/medium/high)

Format your response as JSON:
{
  "steps": [
    {
      "id": "step_1",
      "title": "Step title",
      "action": "What to do",
      "dependencies": [],
      "successCriteria": "How to know it's done",
      "complexity": "low|medium|high"
    }
  ],
  "assumptions": ["Any assumptions made"],
  "notes": "Optional notes about the plan"
}

Be concise. Only include steps that require tool use or significant work.`;
/**
 * Check if planning is needed for this goal
 */
export function shouldGeneratePlan(goal, existingPlan, config) {
    if (!config.enabled)
        return false;
    if (existingPlan && existingPlan.status === "active")
        return false;
    const lowerGoal = goal.toLowerCase();
    // ═══════════════════════════════════════════════════════════════════════════
    // INTENT DETECTION - Explicit planning requests trigger immediately
    // ═══════════════════════════════════════════════════════════════════════════
    // Direct planning verbs (user explicitly wants a plan)
    const explicitPlanningPatterns = [
        /\bplan\b/i, // "plan a website", "help me plan"
        /\bplanning\b/i, // "I need help planning"
        /\bfigure out\b/i, // "figure out how to..."
        /\bhelp me\b/i, // "help me build...", "help me create..."
        /\bwhat('s| is) the best way\b/i, // "what's the best way to..."
        /\bhow (should|do|can|would) (i|we)\b/i, // "how should I...", "how do I..."
        /\bwhat steps\b/i, // "what steps do I need..."
        /\bwalk me through\b/i, // "walk me through..."
        /\bguide me\b/i, // "guide me through..."
        /\bbreak (it |this )?down\b/i, // "break it down", "break this down"
        /\bstep.by.step\b/i, // "do this step by step"
        /\boutline\b/i, // "outline the process"
        /\bstrategy for\b/i, // "strategy for building..."
        /\bapproach to\b/i, // "best approach to..."
        /\bi need to\b/i, // "I need to build..."
        /\bi want to\b/i, // "I want to create..."
    ];
    if (explicitPlanningPatterns.some(p => p.test(goal))) {
        return true;
    }
    // ═══════════════════════════════════════════════════════════════════════════
    // TASK COMPLEXITY - Multi-step tasks that benefit from planning
    // ═══════════════════════════════════════════════════════════════════════════
    // Complex action verbs (tasks that typically require multiple steps)
    const complexVerbs = /\b(build|create|develop|implement|design|setup|set up|configure|deploy|migrate|refactor|integrate|automate|architect|establish|construct|launch|ship)\b/i;
    // Sequential/multi-part indicators
    const sequentialIndicators = [
        goal.includes(" and "), // "X and Y"
        goal.includes(" then "), // "X then Y"
        goal.includes(", then"), // "X, then Y"
        /\bfirst\b.*\bthen\b/i.test(goal), // "first... then..."
        /\bafter\b.*\b(do|create|make)\b/i.test(goal), // "after X, do Y"
    ];
    // Task nouns that typically require multi-step work
    const complexTaskNouns = /\b(api|website|site|app|application|service|system|database|server|pipeline|workflow|bot|agent|project|dashboard|interface|platform|infrastructure)\b/i;
    // Complexity indicators
    const complexityIndicators = [
        goal.length > 100, // Long request
        goal.split(/[.!?]/).filter(Boolean).length > 2, // Multiple sentences  
        complexVerbs.test(goal) && complexTaskNouns.test(goal), // Complex verb + task noun
        /\bfull\b|\bcomplete\b|\bentire\b|\bwhole\b/i.test(goal), // Scope words
        /\bproduction\b|\bprod\b/i.test(goal), // Production deployment
        /\bfrom scratch\b/i.test(goal), // Starting fresh
        /\bend.to.end\b|\be2e\b/i.test(goal), // End-to-end
        /\bnew\b/i.test(goal) && complexVerbs.test(goal), // "new" + complex verb
    ];
    // Count indicators
    const sequentialScore = sequentialIndicators.filter(Boolean).length;
    const complexityScore = complexityIndicators.filter(Boolean).length;
    // Plan if: any sequential indicator OR 1+ complexity indicators
    return sequentialScore >= 1 || complexityScore >= 1;
}
/**
 * Generate an execution plan
 */
export async function generatePlan(goal, context, config, llmCall) {
    const prompt = PLAN_GENERATION_PROMPT
        .replace("{goal}", goal)
        .replace("{maxSteps}", String(config.maxPlanSteps));
    const response = await llmCall({
        messages: [
            { role: "system", content: "You are a planning assistant. Output valid JSON only." },
            { role: "user", content: `${prompt}\n\nContext:\n${context}` },
        ],
        maxTokens: 1500,
    });
    // Parse the response
    const parsed = parseJsonFromResponse(response.content);
    if (!parsed || !Array.isArray(parsed.steps)) {
        // Fallback: single-step plan
        return {
            id: generatePlanId(),
            goal,
            steps: [{
                    id: "step_1",
                    title: "Execute request",
                    action: goal,
                    dependencies: [],
                    successCriteria: "Request completed successfully",
                    complexity: "medium",
                    status: "pending",
                }],
            assumptions: [],
            createdAt: Date.now(),
            status: "active",
        };
    }
    const steps = parsed.steps.map((s, i) => ({
        id: s.id || `step_${i + 1}`,
        title: s.title || `Step ${i + 1}`,
        action: s.action || "",
        dependencies: s.dependencies || [],
        successCriteria: s.successCriteria || "",
        complexity: s.complexity || "medium",
        status: "pending",
    }));
    return {
        id: generatePlanId(),
        goal,
        steps,
        assumptions: parsed.assumptions || [],
        createdAt: Date.now(),
        status: "active",
    };
}
// ============================================================================
// Reflection
// ============================================================================
const REFLECTION_PROMPT = `Given your plan and the last action result, assess progress.

Plan: {plan}

Last action: {action}
Result: {result}

Answer concisely in JSON:
{
  "actionSucceeded": true|false|"partial",
  "onTrack": true|false,
  "decision": "continue"|"replan"|"escalate",
  "reason": "Brief explanation if decision is not 'continue'"
}`;
/**
 * Reflect on progress after a tool execution
 */
export async function reflect(plan, lastAction, result, config, llmCall) {
    if (!config.reflectionAfterTools) {
        // Skip reflection, assume success
        return {
            actionSucceeded: result.success,
            onTrack: result.success,
            decision: result.success ? "continue" : "replan",
        };
    }
    const planSummary = plan.steps
        .map((s, i) => `${i + 1}. [${s.status}] ${s.title}`)
        .join("\n");
    const prompt = REFLECTION_PROMPT
        .replace("{plan}", planSummary)
        .replace("{action}", `${lastAction.name}(${JSON.stringify(lastAction.arguments)})`)
        .replace("{result}", result.error || JSON.stringify(result.output ?? "success"));
    try {
        const response = await llmCall({
            messages: [
                { role: "system", content: "You are assessing progress. Output valid JSON only." },
                { role: "user", content: prompt },
            ],
            maxTokens: 300,
        });
        const parsed = parseJsonFromResponse(response.content);
        if (!parsed) {
            return {
                actionSucceeded: result.success,
                onTrack: result.success,
                decision: result.success ? "continue" : "replan",
            };
        }
        return {
            actionSucceeded: parsed.actionSucceeded ?? result.success,
            onTrack: parsed.onTrack ?? result.success,
            decision: parsed.decision ?? "continue",
            reason: parsed.reason,
        };
    }
    catch {
        // Reflection failed, continue anyway
        return {
            actionSucceeded: result.success,
            onTrack: result.success,
            decision: result.success ? "continue" : "replan",
        };
    }
}
// ============================================================================
// Replanning
// ============================================================================
const REPLAN_PROMPT = `The current plan needs adjustment.

Original plan:
{originalPlan}

Reason for replanning: {reason}

Current status:
- Completed: {completed}
- Remaining: {remaining}

Create a revised plan that addresses the issue. Keep completed steps, adjust remaining ones.

Output valid JSON with the same format as the original plan.`;
/**
 * Revise the plan based on reflection
 */
export async function replan(plan, reason, config, llmCall) {
    const completed = plan.steps
        .filter((s) => s.status === "complete")
        .map((s) => s.title)
        .join(", ") || "none";
    const remaining = plan.steps
        .filter((s) => s.status !== "complete")
        .map((s) => s.title)
        .join(", ") || "none";
    const originalPlan = plan.steps
        .map((s, i) => `${i + 1}. [${s.status}] ${s.title}: ${s.action}`)
        .join("\n");
    const prompt = REPLAN_PROMPT
        .replace("{originalPlan}", originalPlan)
        .replace("{reason}", reason)
        .replace("{completed}", completed)
        .replace("{remaining}", remaining);
    try {
        const response = await llmCall({
            messages: [
                { role: "system", content: "You are revising a plan. Output valid JSON only." },
                { role: "user", content: prompt },
            ],
            maxTokens: 1500,
        });
        const parsed = parseJsonFromResponse(response.content);
        if (!parsed || !Array.isArray(parsed.steps)) {
            // Keep existing plan
            return plan;
        }
        // Preserve completed steps, merge new steps
        const completedSteps = plan.steps.filter((s) => s.status === "complete");
        const newSteps = parsed.steps.map((s, i) => ({
            id: s.id || `step_${completedSteps.length + i + 1}`,
            title: s.title || `Step ${i + 1}`,
            action: s.action || "",
            dependencies: s.dependencies || [],
            successCriteria: s.successCriteria || "",
            complexity: s.complexity || "medium",
            status: "pending",
        }));
        return {
            ...plan,
            steps: [...completedSteps, ...newSteps],
            createdAt: Date.now(), // Update timestamp
        };
    }
    catch {
        // Replanning failed, keep existing
        return plan;
    }
}
// ============================================================================
// Plan Updates
// ============================================================================
/**
 * Mark a plan step as complete
 */
export function completeStep(plan, stepId, result) {
    const steps = plan.steps.map((s) => s.id === stepId ? { ...s, status: "complete", result } : s);
    // Check if all steps complete
    const allComplete = steps.every((s) => s.status === "complete");
    return {
        ...plan,
        steps,
        status: allComplete ? "completed" : plan.status,
    };
}
/**
 * Mark a plan step as failed
 */
export function failStep(plan, stepId, error) {
    const steps = plan.steps.map((s) => s.id === stepId ? { ...s, status: "failed", result: error } : s);
    return {
        ...plan,
        steps,
    };
}
/**
 * Get the next pending step
 */
export function getNextStep(plan) {
    // Find first pending step with no pending dependencies
    for (const step of plan.steps) {
        if (step.status !== "pending")
            continue;
        const depsComplete = step.dependencies.every((depId) => {
            const dep = plan.steps.find((s) => s.id === depId);
            return dep?.status === "complete";
        });
        if (depsComplete)
            return step;
    }
    return null;
}
/**
 * Format plan for context injection
 */
export function formatPlanForContext(plan) {
    const lines = [
        "## Execution Plan",
        "",
        `**Goal:** ${plan.goal}`,
        "",
        "### Steps",
    ];
    for (const step of plan.steps) {
        const status = step.status === "complete" ? "✓" :
            step.status === "in_progress" ? "◐" :
                step.status === "failed" ? "✗" : "○";
        lines.push(`${status} **${step.title}**`);
        lines.push(`  - Action: ${step.action}`);
        lines.push(`  - Success: ${step.successCriteria}`);
        if (step.result) {
            lines.push(`  - Result: ${step.result}`);
        }
    }
    if (plan.assumptions.length > 0) {
        lines.push("");
        lines.push("### Assumptions");
        for (const assumption of plan.assumptions) {
            lines.push(`- ${assumption}`);
        }
    }
    return lines.join("\n");
}
// ============================================================================
// Utilities
// ============================================================================
function generatePlanId() {
    return `plan_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}
function parseJsonFromResponse(content) {
    try {
        // Try direct parse first
        return JSON.parse(content);
    }
    catch {
        // Try to extract JSON from markdown code block
        const match = content.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
        if (match) {
            try {
                return JSON.parse(match[1]);
            }
            catch {
                return null;
            }
        }
        return null;
    }
}
//# sourceMappingURL=planner.js.map