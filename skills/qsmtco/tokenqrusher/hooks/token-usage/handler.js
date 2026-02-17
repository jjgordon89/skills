/**
 * Token Usage Hook - Refactored to use shared module
 * 
 * Uses: shared.getStatusEmoji, shared.loadConfigCached
 */
'use strict';

const { execSync } = require('child_process');
const { existsSync, readFileSync } = require('fs');
const { join } = require('path');
const shared = require('../token-shared/shared');

/**
 * Gets current session cost from OpenClaw
 * @returns {number|null}
 */
const getSessionCost = () => {
    try {
        const result = execSync('openclaw session status --json 2>/dev/null', {
            encoding: 'utf-8',
            timeout: 5000,
            maxBuffer: 10 * 1024
        });
        
        if (result) {
            const data = JSON.parse(result);
            if (data.usage?.cost) {
                return parseFloat(data.usage.cost);
            }
        }
    } catch (e) {
        // Ignore errors
    }
    return null;
};

/**
 * Gets today's usage from tracker
 * @returns {number|null}
 */
const getTodayUsage = () => {
    try {
        const statePath = join(process.env.HOME || '/home/q', '.openclaw/workspace/memory/usage-history.json');
        
        if (existsSync(statePath)) {
            const data = JSON.parse(readFileSync(statePath, 'utf-8'));
            
            const today = new Date().toISOString().split('T')[0];
            let total = 0;
            
            for (const record of data) {
                if (record.timestamp && record.timestamp.startsWith(today)) {
                    total += record.cost || 0;
                }
            }
            
            return total;
        }
    } catch (e) {
        // Ignore
    }
    return null;
};

/**
 * Main handler function
 * @param {Object} event
 * @returns {Promise<void>}
 */
async function handler(event) {
    // Entry log
    console.log('[token-usage] Entry: handler');

    // Guard: Only handle agent:bootstrap
    if (event.type !== 'agent' || event.action !== 'bootstrap') {
        return;
    }

    // Load config with caching
    const config = shared.loadConfigCached((msg) => console.log(msg));
    
    // Guard: Hook disabled
    if (config.enabled === false) {
        console.log('[token-usage] Exit: disabled');
        return;
    }

    // Get budgets
    const budgets = config.budgets || { daily: 5.0, weekly: 30.0, monthly: 100.0 };
    const dailyLimit = budgets.daily || 5.0;
  
    // Try to get current usage
    const sessionCost = getSessionCost();
    const todayUsage = getTodayUsage();
    
    // Calculate percentage with division by zero protection
    const currentCost = todayUsage || sessionCost || 0;
    const percent = dailyLimit > 0 ? currentCost / dailyLimit : 0;
    
    // Use shared pure function for emoji
    const emoji = shared.getStatusEmoji(percent);
    
    // Log status
    console.log(`[token-usage] ${emoji} Budget: $${currentCost.toFixed(2)} / $${dailyLimit} (${(percent * 100).toFixed(0)}%)`);

    // Add warnings for high usage
    const warningThreshold = config.warningThreshold || 0.8;
    const criticalThreshold = config.criticalThreshold || 0.95;
    
    if (percent >= criticalThreshold) {
        console.log(`[token-usage] 🔴 CRITICAL: Budget at ${(percent * 100).toFixed(0)}% - Consider using free model`);
    } else if (percent >= warningThreshold) {
        console.log(`[token-usage] 🟡 Warning: Budget at ${(percent * 100).toFixed(0)}%`);
    }
    
    console.log('[token-usage] Exit: success');
}

/**
 * Export for OpenClaw
 */
module.exports = handler;
module.exports.default = handler;
