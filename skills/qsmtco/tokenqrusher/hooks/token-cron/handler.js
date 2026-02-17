/**
 * Token Cron Hook - Periodic optimization execution
 * 
 * Listens to: gateway:startup
 * 
 * Triggers scheduled optimization on gateway startup.
 */

const { readFileSync, existsSync } = require('fs');
const { join, dirname } = require('path');
const { execSync } = require('child_process');

/**
 * Load configuration
 */
function loadConfig() {
  const configPath = join(dirname(__filename), 'config.json');
  
  if (existsSync(configPath)) {
    try {
      return JSON.parse(readFileSync(configPath, 'utf-8'));
    } catch (e) {
      console.error('[token-cron] Config error:', e.message);
    }
  }
  
  return { 
    enabled: true, 
    runOnStartup: true,
    optimizeOnStartup: true,
    checkBudgetOnStartup: true
  };
}

/**
 * Run optimization script
 */
function runOptimization() {
  try {
    const scriptPath = join(process.env.HOME || '/home/q', 
      '.openclaw/workspace/skills/tokenQrusher/scripts/cron-optimizer/optimizer.py');
    
    if (existsSync(scriptPath)) {
      const result = execSync(`python3 "${scriptPath}" run --trigger startup`, {
        encoding: 'utf-8',
        timeout: 30000,
        maxBuffer: 10 * 1024
      });
      
      console.log('[token-cron] Optimization run:', result.trim());
      return true;
    }
  } catch (e) {
    console.error('[token-cron] Optimization failed:', e.message);
  }
  return false;
}

/**
 * Check budget status
 */
function checkBudget() {
  try {
    const scriptPath = join(process.env.HOME || '/home/q',
      '.openclaw/workspace/skills/tokenQrusher/scripts/usage/cli.py');
    
    if (existsSync(scriptPath)) {
      const result = execSync(`python3 "${scriptPath}" budget --period daily --json`, {
        encoding: 'utf-8',
        timeout: 10000,
        maxBuffer: 10 * 1024
      });
      
      const data = JSON.parse(result);
      
      // Log status with emoji
      const percent = data.percent || 0;
      let emoji = '✅';
      
      if (percent >= 1.0) emoji = '🚨';
      else if (percent >= 0.95) emoji = '🔴';
      else if (percent >= 0.80) emoji = '🟡';
      
      console.log(`[token-cron] ${emoji} Budget: $${data.spent?.toFixed(2)} / $${data.limit} (${(percent * 100).toFixed(0)}%)`);
      return true;
    }
  } catch (e) {
    // Budget check failure is non-fatal
    console.log('[token-cron] Budget check skipped (no data)');
  }
  return false;
}

/**
 * Main handler
 */
async function handler(event) {
  // Only handle gateway:startup
  if (event.type !== 'gateway' || event.action !== 'startup') {
    return;
  }

  const config = loadConfig();
  
  if (config.enabled === false) {
    return;
  }

  console.log('[token-cron] Gateway started, running scheduled tasks');

  // Run startup tasks
  if (config.runOnStartup) {
    if (config.optimizeOnStartup) {
      runOptimization();
    }
    
    if (config.checkBudgetOnStartup) {
      checkBudget();
    }
  }
}

/**
 * Export for OpenClaw
 */
module.exports = handler;
module.exports.default = handler;
