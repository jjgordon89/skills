/**
 * Token Model Hook - Refactored to use shared module
 * 
 * Uses: shared.classifyForModel, shared.getModelForTier, shared.getTierCost
 *       shared.extractUserMessage, shared.loadConfigCached
 */
'use strict';

const shared = require('../token-shared/shared');

/**
 * Main handler function
 * @param {Object} event
 * @returns {Promise<void>}
 */
async function handler(event) {
    // Entry log
    console.log('[token-model] Entry: handler');

    // Guard: Only handle agent:bootstrap
    if (event.type !== 'agent' || event.action !== 'bootstrap') {
        return;
    }

    // Load config with caching
    const config = shared.loadConfigCached((msg) => console.log(msg));
    
    // Guard: Hook disabled
    if (config.enabled === false) {
        console.log('[token-model] Exit: disabled');
        return;
    }

    // Guard: No context
    const context = event.context;
    if (!context) {
        console.log('[token-model] Exit: no context');
        return;
    }

    // Extract message using shared pure function
    const messageResult = shared.extractUserMessage(context);
    if (!messageResult.isJust) {
        console.log('[token-model] Exit: no message');
        return;
    }

    const message = messageResult.value;

    // Classify for model using shared pure function
    const classification = shared.classifyForModel(message);
    const recommendedModel = shared.getModelForTier(classification.tier, config.models);
    const modelCost = shared.getTierCost(classification.tier);

    // Log recommendation
    const emoji = classification.tier === 'quick' ? '⚡' : 
                 classification.tier === 'standard' ? '💡' : '🧠';
    
    console.log(`[token-model] ${emoji} Model: ${classification.tier} → ${recommendedModel} (${modelCost})`);
    console.log('[token-model] Exit: success');
}

/**
 * Export for OpenClaw
 */
module.exports = handler;
module.exports.default = handler;
