/**
 * Context Classifier - Message complexity classification for context filtering
 * 
 * Classifies user messages to determine how much context should be loaded.
 * This is the core logic that powers the token-context hook.
 */

// Communication patterns that indicate simple messages (greetings, acknowledgments)
const SIMPLE_PATTERNS = [
  /^(hi|hey|hello|yo|sup|howdy)\b/i,
  /^(thanks|thank you|thx|ty)\b/i,
  /^(ok|okay|sure|got it|understood|roger|affirmative)\b/i,
  /^(yes|yeah|yep|yup|no|nope|nah)\b/i,
  /^(good|great|nice|cool|awesome|amazing|wonderful|perfect)\b/i,
  /^(what|how)'s?\s+(up|it\s+going|going\s+on)/i,
  /^(see|heard|looking)\s+(you|u)\b/i,
  /^(lol|haha|lmao|rofl)\b/i,
  /^(sorry|apologies|my\s+bad)\b/i,
  /^\p{Emoji}/u,  // Starts with emoji
  /^\.{2,}$/,     // Just dots
  /^\?+$/,        // Just question marks
];

// Single short words (likely simple queries)
const SHORT_WORD_PATTERN = /^\p{L}{1,15}$/u;

// Background task patterns (treated as simple - no reasoning needed)
const BACKGROUND_PATTERNS = [
  /^heartbeat$/i,
  /^check\s+(email|calendar|weather|monitoring|logs?)\b/i,
  /^(cron|scheduled)\s+task/i,
  /^parse\s+(csv|json|log|xml|file)\b/i,
  /^extract\s+\w+\s+from/i,
  /^read\s+(log|logs|file)\b/i,
  /^scan\s+(file|document|error|logs?)\b/i,
  /^list\s+(files|dir|directory)\b/i,
  /^show\s+status$/i,
  /^get\s+(status|info)\b/i,
];

// Complex task indicators (need full context)
const COMPLEX_PATTERNS = [
  /^(design|architect)\s+\w+/i,
  /\barchitect(?:ure|ing)?\b/i,
  /\bcomprehensive\b/i,
  /\banalyze\s+deeply\b/i,
  /\bplan\s+\w+\s+system\b/i,
  /\bcreate\s+\w+\s+from\s+scratch\b/i,
  /\brefactor\s+completely\b/i,
  /\bimplement\s+(full|entire)\b/i,
  /\boptimize\s+(performance|speed|scale)\b/i,
  /\bdebug\s+(complex|difficult|hard)\b/i,
  /\bfix\s+(entire|whole|complex)\b/i,
  /\bbuild\s+(from|from\s+scratch)\b/i,
  /\bwrite\s+(complex|advanced|production)\b/i,
];

// Keywords that might indicate standard work (not simple, not complex)
const STANDARD_KEYWORDS = [
  'write', 'create', 'edit', 'update', 'add', 'remove', 'delete',
  'fix', 'debug', 'explain', 'how', 'what', 'why', 'when', 'where',
  'find', 'search', 'replace', 'rename', 'move', 'copy'
];

/**
 * Complexity levels for context filtering
 */
export type ComplexityLevel = 'simple' | 'standard' | 'complex';

/**
 * Configuration for file lists per complexity level
 */
export interface ContextConfig {
  files?: {
    simple?: string[];
    standard?: string[];
    complex?: string[];
  };
  enabled?: boolean;
  logLevel?: 'debug' | 'info' | 'warn';
}

/**
 * Result of classification
 */
export interface ClassificationResult {
  level: ComplexityLevel;
  confidence: number;
  matchedPattern?: string;
  reasoning: string;
}

/**
 * Classifies message complexity for context filtering
 * 
 * @param message - The user's message to classify
 * @returns ComplexityLevel indicating how much context to load
 */
export function classifyComplexity(message: string): ClassificationResult {
  if (!message || typeof message !== 'string') {
    return {
      level: 'standard',
      confidence: 0,
      reasoning: 'Empty or invalid message, defaulting to standard'
    };
  }

  const trimmed = message.trim();
  const lower = trimmed.toLowerCase();

  // Empty after trim = standard
  if (trimmed.length === 0) {
    return {
      level: 'standard',
      confidence: 0,
      reasoning: 'Empty message, defaulting to standard'
    };
  }

  // Check simple patterns first (greetings, acknowledgments)
  for (const pattern of SIMPLE_PATTERNS) {
    if (pattern.test(trimmed)) {
      return {
        level: 'simple',
        confidence: 0.95,
        matchedPattern: pattern.source,
        reasoning: `Matched simple pattern: ${pattern.source}`
      };
    }
  }

  // Check short single-word messages
  if (SHORT_WORD_PATTERN.test(trimmed) && !STANDARD_KEYWORDS.some(k => lower.includes(k))) {
    return {
      level: 'simple',
      confidence: 0.8,
      reasoning: 'Short single word without work-related keywords'
    };
  }

  // Check background tasks (treated as simple)
  for (const pattern of BACKGROUND_PATTERNS) {
    if (pattern.test(lower)) {
      return {
        level: 'simple',
        confidence: 0.85,
        matchedPattern: pattern.source,
        reasoning: `Matched background task pattern: ${pattern.source}`
      };
    }
  }

  // Check complex patterns
  for (const pattern of COMPLEX_PATTERNS) {
    if (pattern.test(lower)) {
      return {
        level: 'complex',
        confidence: 0.9,
        matchedPattern: pattern.source,
        reasoning: `Matched complex pattern: ${pattern.source}`
      };
    }
  }

  // Default to standard
  return {
    level: 'standard',
    confidence: 0.6,
    reasoning: 'No specific pattern matched, defaulting to standard'
  };
}

/**
 * Get list of allowed files for a complexity level
 * 
 * @param level - The complexity level
 * @param config - Optional configuration with custom file lists
 * @returns Array of file names to load
 */
export function getAllowedFiles(level: ComplexityLevel, config?: ContextConfig): string[] {
  // Default file lists
  const defaults: Record<ComplexityLevel, string[]> = {
    simple: ['SOUL.md', 'IDENTITY.md'],
    standard: ['SOUL.md', 'IDENTITY.md', 'USER.md'],
    complex: ['SOUL.md', 'IDENTITY.md', 'USER.md', 'TOOLS.md', 'AGENTS.md', 'MEMORY.md', 'HEARTBEAT.md']
  };

  // Check config for custom files
  if (config?.files?.[level]) {
    return config.files[level]!;
  }

  return defaults[level];
}

/**
 * Get all possible bootstrap files (for complex level)
 */
export function getAllFiles(): string[] {
  return [
    'SOUL.md',
    'IDENTITY.md', 
    'USER.md',
    'TOOLS.md',
    'AGENTS.md',
    'MEMORY.md',
    'HEARTBEAT.md'
  ];
}

/**
 * Validate that a file name is safe (prevent path traversal)
 */
export function isValidFileName(name: string): boolean {
  // Only allow alphanumeric, dots, dashes, underscores
  return /^[a-zA-Z0-9._-]+$/.test(name) && name.length <= 255;
}

// Export for use in handler
export default {
  classifyComplexity,
  getAllowedFiles,
  getAllFiles,
  isValidFileName
};
