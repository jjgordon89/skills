/**
 * Token Context Hook - Main Handler
 * 
 * OpenClaw hook that filters context files based on message complexity.
 * Listens to: agent:bootstrap
 * 
 * This hook runs before workspace files are injected into the context,
 * allowing us to filter which files are loaded based on the user's message.
 */

import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';

// Import classifier
import { 
  classifyComplexity, 
  getAllowedFiles, 
  isValidFileName,
  type ClassificationResult,
  type ComplexityLevel 
} from './classifier.js';

/**
 * Hook handler interface (simplified for this implementation)
 */
interface HookEvent {
  type: string;
  action: string;
  sessionKey: string;
  timestamp: Date;
  messages?: string[];
  context?: HookContext;
}

interface HookContext {
  sessionEntry?: {
    messages?: Array<{ role: string; content: string }>;
    lastMessage?: string;
  };
  sessionId?: string;
  workspaceDir?: string;
  bootstrapFiles?: Array<{
    name: string;
    path: string;
    raw?: string;
    injected?: string;
  }>;
  cfg?: Record<string, unknown>;
}

/**
 * Hook configuration
 */
interface HookConfig {
  files?: {
    simple?: string[];
    standard?: string[];
    complex?: string[];
  };
  enabled?: boolean;
  logLevel?: 'debug' | 'info' | 'warn';
  dryRun?: boolean;
}

/**
 * Load hook configuration from config.json
 */
function loadConfig(): HookConfig {
  const configPath = join(dirname(__filename), 'config.json');
  
  if (existsSync(configPath)) {
    try {
      const content = readFileSync(configPath, 'utf-8');
      const config = JSON.parse(content);
      
      // Validate config
      if (typeof config.enabled !== 'undefined' && typeof config.enabled !== 'boolean') {
        console.warn('[token-context] Warning: config.enabled must be boolean');
        config.enabled = true;
      }
      
      return config;
    } catch (e) {
      console.error('[token-context] Failed to parse config.json:', e);
    }
  }
  
  // Default configuration
  return { 
    enabled: true, 
    logLevel: 'info' 
  };
}

/**
 * Extract the user's most recent message from the session context
 */
function extractUserMessage(context?: HookContext): string | null {
  if (!context) return null;
  
  // Try to get message from session entry
  const sessionEntry = context.sessionEntry;
  if (!sessionEntry) return null;
  
  // Method 1: Get messages array and find last user message
  if (sessionEntry.messages && Array.isArray(sessionEntry.messages)) {
    // Search from end to get most recent user message
    for (let i = sessionEntry.messages.length - 1; i >= 0; i--) {
      const msg = sessionEntry.messages[i];
      if (msg && msg.role === 'user' && msg.content) {
        return msg.content;
      }
    }
  }
  
  // Method 2: Try lastMessage field
  if (sessionEntry.lastMessage) {
    return sessionEntry.lastMessage;
  }
  
  return null;
}

/**
 * Main hook handler
 * This function is called by OpenClaw when the hook is triggered
 */
export async function handler(event: HookEvent): Promise<void> {
  // Only handle agent:bootstrap events
  if (event.type !== 'agent' || event.action !== 'bootstrap') {
    return;
  }

  const config = loadConfig();
  
  // Check if hook is disabled
  if (config.enabled === false) {
    if (config.logLevel === 'debug') {
      console.log('[token-context] Hook disabled, skipping');
    }
    return;
  }

  // Get context
  const context = event.context;
  if (!context) {
    if (config.logLevel === 'debug') {
      console.log('[token-context] No context available');
    }
    return;
  }

  // Extract user message
  const message = extractUserMessage(context);
  
  if (!message) {
    // No message found - can't classify - use standard context
    if (config.logLevel !== 'warn') {
      // Only log if not silent
    }
    return;
  }

  // Classify message complexity
  const classification: ClassificationResult = classifyComplexity(message);
  
  // Get allowed files for this complexity level
  const allowedFiles = getAllowedFiles(classification.level, config);
  
  // Get current bootstrap files
  const currentFiles = context.bootstrapFiles || [];
  const currentFileNames = currentFiles.map(f => f.name);

  // Filter to only allowed files
  const filteredFiles = currentFiles.filter(f => {
    // Validate file name for security
    if (!isValidFileName(f.name)) {
      console.warn(`[token-context] Skipping invalid file name: ${f.name}`);
      return false;
    }
    return allowedFiles.includes(f.name);
  });

  // Determine which files were removed
  const removed = currentFileNames.filter(f => !allowedFiles.includes(f));
  
  // Log results
  if (config.logLevel === 'debug') {
    console.log('[token-context] === Context Filtering Debug ===');
    console.log(`[token-context] Message: "${message.substring(0, 100)}${message.length > 100 ? '...' : ''}"`);
    console.log(`[token-context] Classification: ${classification.level} (confidence: ${classification.confidence})`);
    console.log(`[token-context] Reasoning: ${classification.reasoning}`);
    console.log(`[token-context] Allowed files: ${allowedFiles.join(', ')}`);
    console.log(`[token-context] Current files: ${currentFileNames.join(', ')}`);
  }

  // Always log summary at info level
  if (removed.length > 0) {
    console.log(`[token-context] 📉 Context filtered: ${currentFileNames.length} → ${filteredFiles.length} files`);
    console.log(`[token-context]    Removed: ${removed.join(', ')}`);
  } else {
    console.log(`[token-context] ✓ Context: ${filteredFiles.length} files (${classification.level})`);
  }

  // Apply filtered list (unless dry run)
  if (!config.dryRun) {
    context.bootstrapFiles = filteredFiles;
  }
}

/**
 * Export default for OpenClaw hook system
 */
export default handler;

// Also export handler as named export for flexibility
module.exports = { handler };
module.exports.default = handler;
