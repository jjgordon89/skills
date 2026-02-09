const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// [2026-02-03] WRAPPER REFACTOR: PURE PROXY
// This wrapper now correctly delegates to the core 'evolver' plugin.
// Enhanced with Kill Switch, Heartbeat Summary, Artifact Upload, and Thought Injection.

function sleepSeconds(sec) {
    const s = Number(sec);
    if (!Number.isFinite(s) || s <= 0) return;
    try {
        execSync(`sleep ${s}`);
    } catch (_) {
        const waitStart = Date.now();
        while (Date.now() - waitStart < s * 1000) {}
    }
}

function nextCycleTag(cycleFile) {
    let cycleId = 1;
    try {
        if (fs.existsSync(cycleFile)) {
            const raw = fs.readFileSync(cycleFile, 'utf8').trim();
            if (raw && !isNaN(raw)) {
                cycleId = parseInt(raw, 10) + 1;
            }
        }
    } catch (e) {
        console.error('Cycle read error:', e.message);
    }

    try {
        fs.writeFileSync(cycleFile, cycleId.toString());
    } catch (e) {
        console.error('Cycle write error:', e.message);
    }

    return String(cycleId).padStart(4, '0');
}

function tailText(buf, maxChars) {
    if (!buf) return '';
    const s = Buffer.isBuffer(buf) ? buf.toString('utf8') : String(buf);
    if (s.length <= maxChars) return s;
    return s.slice(-maxChars);
}

// --- FEATURE 2: HEARTBEAT SUMMARY (Option 2: Real-time Error, Summary Info) ---
let sessionLogs = { infoCount: 0, errorCount: 0, startTime: 0, errors: [] };

// Lifecycle log target group (set via env or hardcode for reliability)
const FEISHU_LOG_GROUP = process.env.LOG_TARGET || 'oc_ab79ebbe224701d0288891d6f8ddb10e';
const FEISHU_CN_REPORT_GROUP = process.env.FEISHU_CN_REPORT_GROUP || 'oc_86ff5e0d40cb49c777a24156f379c48c';
process.env.LOG_TARGET = FEISHU_LOG_GROUP;

function forwardLogToFeishu(msg, type = 'INFO') {
    // Avoid re-forwarding Feishu forward errors
    if (msg.includes('[FeishuForwardFail]') || msg.includes('[CardFail]')) return;
    if (!msg || !msg.trim()) return;

    if (type === 'ERROR') {
        sessionLogs.errorCount++;
        sessionLogs.errors.push(msg.slice(0, 300));
        sendCardInternal(msg, 'ERROR');
    } else if (type === 'LIFECYCLE') {
        // Key lifecycle events: always forward
        sendCardInternal(msg, 'INFO');
    } else {
        sessionLogs.infoCount++;
        // Regular INFO: silent (too noisy for group chat)
    }
}

function sendCardInternal(msg, type) {
    try {
        const script = path.resolve(__dirname, 'send-card-cli.js');
        if (!fs.existsSync(script)) return;

        const tmpFile = path.join('/tmp', `feishu_log_${Date.now()}_${Math.random().toString(36).slice(2)}.txt`);
        fs.writeFileSync(tmpFile, msg);

        execSync(`node "${script}" "$(cat ${tmpFile})" "[${type}]"`, {
            stdio: 'ignore', 
            timeout: 5000,
            env: process.env
        });
        
        fs.unlinkSync(tmpFile);
    } catch (e) {
        // ignore
    }
}

function sendSummary(cycleTag, duration, success) {
    const statusIcon = success ? '✅' : '❌';
    const persona = success ? 'greentea' : 'maddog';
    // duration needs to be parsed as number for comparison
    const durNum = parseFloat(duration);
    const comment = getComment('summary', durNum, success, persona);

    const errorSection = sessionLogs.errors.length > 0 
        ? `\n\n**Recent Errors:**\n${sessionLogs.errors.slice(-3).map(e => `> ${e}`).join('\n')}` 
        : '';
    
    const summaryMsg = `**Cycle #${cycleTag} Complete**\n` +
        `Status: ${statusIcon} ${success ? 'Success' : 'Failed'}\n` +
        `Duration: ${duration}s\n` +
        `Logs: ${sessionLogs.infoCount} Info, ${sessionLogs.errorCount} Error\n` +
        `💭 *${comment}*` +
        errorSection;

    sendCardInternal(summaryMsg, success ? 'SUMMARY' : 'FAILURE');
}

// --- FEATURE 5: GIT SYNC (Safety Net) ---
// Lazy-load optional modules with fallbacks to prevent startup crashes.
let selfRepair = null;
let getComment = (_type, _dur, _ok, _persona) => '';
try {
    selfRepair = require('./self-repair.js');
} catch (e) {
    console.warn('[Wrapper] self-repair.js not found, git repair disabled.');
}
try {
    const commentary = require('./commentary.js');
    if (typeof commentary.getComment === 'function') getComment = commentary.getComment;
} catch (e) {
    console.warn('[Wrapper] commentary.js not found, using silent mode.');
}

// Issue tracker: records problems to a Feishu doc
let issueTracker = null;
try {
    issueTracker = require('./issue_tracker.js');
} catch (e) {
    console.warn('[Wrapper] issue_tracker.js not found, issue tracking disabled.');
}

// gitSync runs after every successful evolution cycle (no cooldown).

function execWithTimeout(cmd, cwd, timeoutMs = 30000) {
    try {
        // Use stdio: 'pipe' to capture output for error reporting, but ignore it for success
        execSync(cmd, { cwd, timeout: timeoutMs, stdio: 'pipe' });
    } catch (e) {
        // e.message usually contains the command output if stdio is pipe
        throw new Error(`Command "${cmd}" failed or timed out: ${e.message}`);
    }
}

function buildCommitMessage(statusOutput, cwd) {
    const lines = statusOutput.split('\n').filter(Boolean);
    const added = [];
    const modified = [];
    const deleted = [];

    for (const line of lines) {
        const code = line.substring(0, 2).trim();
        const file = line.substring(3).trim();
        // Skip logs, temp, and non-essential files
        if (file.startsWith('logs/') || file.startsWith('temp/') || file.endsWith('.log')) continue;
        if (code.includes('A') || code === '??') added.push(file);
        else if (code.includes('D')) deleted.push(file);
        else modified.push(file);
    }

    // Summarize by skill/directory
    const skillChanges = new Map();
    for (const f of [...added, ...modified, ...deleted]) {
        const parts = f.split('/');
        let group = parts[0];
        if (parts[0] === 'skills' && parts.length > 1) group = `skills/${parts[1]}`;
        if (!skillChanges.has(group)) skillChanges.set(group, []);
        skillChanges.get(group).push(f);
    }

    const totalFiles = added.length + modified.length + deleted.length;
    if (totalFiles === 0) return '🧬 Evolution: maintenance (no significant changes)';

    // Build title line
    const actions = [];
    if (added.length > 0) actions.push(`${added.length} added`);
    if (modified.length > 0) actions.push(`${modified.length} modified`);
    if (deleted.length > 0) actions.push(`${deleted.length} deleted`);

    const areas = [...skillChanges.keys()].slice(0, 3);
    const areaStr = areas.join(', ') + (skillChanges.size > 3 ? ` (+${skillChanges.size - 3} more)` : '');

    let title = `🧬 Evolution: ${actions.join(', ')} in ${areaStr}`;

    // Build body with file details (keep under 20 lines)
    const bodyLines = [];
    for (const [group, files] of skillChanges) {
        if (files.length <= 3) {
            for (const f of files) bodyLines.push(`- ${f}`);
        } else {
            bodyLines.push(`- ${group}/ (${files.length} files)`);
        }
    }

    if (bodyLines.length > 0) {
        return title + '\n\n' + bodyLines.slice(0, 20).join('\n');
    }
    return title;
}

function gitSync() {
    try {
        console.log('[Wrapper] Executing Git Sync...');
        // Git repo root is .openclaw/ (parent of workspace/)
        const gitRoot = path.resolve(__dirname, '../../../');
        const workspaceRoot = path.resolve(__dirname, '../../');

        // 1. Only stage workspace/ files (not .openclaw root config)
        //    Stage specific safe paths, not everything
        const safePaths = [
            'workspace/skills/',
            'workspace/memory/',
            'workspace/RECENT_EVENTS.md',
            'workspace/TROUBLESHOOTING.md',
            'workspace/TOOLS.md',
            'workspace/assets/',
            'workspace/docs/',
        ];
        for (const p of safePaths) {
            try {
                execWithTimeout(`git add ${p}`, gitRoot, 30000);
            } catch (_) {} // Skip if path doesn't exist
        }

        // 2. Check if there's anything staged
        const status = execSync('git diff --cached --name-only', { cwd: gitRoot, encoding: 'utf8' }).trim();
        if (!status) {
            console.log('[Wrapper] Git Sync: nothing to commit.');
            return;
        }

        // 3. Build descriptive commit message
        const fileCount = status.split('\n').filter(Boolean).length;
        const areas = [...new Set(status.split('\n').filter(Boolean).map(f => {
            const parts = f.split('/');
            if (parts[0] === 'workspace' && parts[1] === 'skills' && parts.length > 2) return `skills/${parts[2]}`;
            if (parts[0] === 'workspace' && parts.length > 1) return parts[1];
            return parts[0];
        }))].slice(0, 3);
        const areaStr = areas.join(', ') + (areas.length >= 3 ? ' ...' : '');
        const commitMsg = `🧬 Evolution: ${fileCount} files in ${areaStr}`;
        const msgFile = path.join('/tmp', `evolver_commit_${Date.now()}.txt`);
        fs.writeFileSync(msgFile, commitMsg);
        execWithTimeout(`git commit -F "${msgFile}"`, gitRoot, 30000);
        try { fs.unlinkSync(msgFile); } catch (_) {}

        // 4. Pull --rebase then push
        try {
            execWithTimeout('git pull origin main --rebase --autostash', gitRoot, 120000);
        } catch (e) {
            console.error('[Wrapper] Pull Rebase Failed:', e.message);
            try {
                if (selfRepair && typeof selfRepair.run === 'function') selfRepair.run();
            } catch (_) {}
            throw e;
        }
        execWithTimeout('git push origin main', gitRoot, 120000);

        console.log('[Wrapper] Git Sync Complete.');
        forwardLogToFeishu(`🧬 Git Sync: ${fileCount} files in ${areaStr}`, 'LIFECYCLE');
    } catch (e) {
        console.error('[Wrapper] Git Sync Failed:', e.message);
        forwardLogToFeishu(`[Wrapper] ⚠️ Git Sync Failed: ${e.message}`, 'ERROR');
    }
}

// --- FEATURE 1: KILL SWITCH ---
const KILL_SWITCH_FILE = path.resolve(__dirname, '../../memory/evolver_kill_switch.lock');
function checkKillSwitch() {
    if (fs.existsSync(KILL_SWITCH_FILE)) {
        console.error(`[Wrapper] Kill Switch Detected at ${KILL_SWITCH_FILE}! Terminating loop.`);
        sendCardInternal(`🛑 **Emergency Stop Triggered!**\nKill switch file detected at ${KILL_SWITCH_FILE}. Wrapper is shutting down.`, 'CRITICAL');
        process.exit(1);
    }
}

// --- FEATURE 4: THOUGHT INJECTION ---
const INJECTION_FILE = path.resolve(__dirname, '../../memory/evolver_hint.txt');
function getInjectionHint() {
    if (fs.existsSync(INJECTION_FILE)) {
        try {
            const hint = fs.readFileSync(INJECTION_FILE, 'utf8').trim();
            if (hint) {
                console.log(`[Wrapper] Injecting Thought: ${hint}`);
                // Delete after reading (one-time injection)
                fs.unlinkSync(INJECTION_FILE); 
                return hint;
            }
        } catch (e) {}
    }
    return null;
}

// --- FEATURE 3: ARTIFACT UPLOAD (Stub) ---
// This requires a more complex 'upload-file' skill or API which we might not have ready.
// For now, we'll just log that artifacts are available locally.
function checkArtifacts(cycleTag) {
    // Logic to find artifacts and maybe just cat them if small?
    // Placeholder for future expansion.
}


// --- FEATURE 6: CLEANUP (Disk Hygiene) ---
let cleanup = null;
try {
    cleanup = require('./cleanup.js');
} catch (e) {
    console.warn('[Wrapper] cleanup.js not found, disk cleanup disabled.');
}

async function run() {
    console.log('Launching Feishu Evolver Wrapper (Proxy Mode)...');
    forwardLogToFeishu('🧬 Wrapper starting up...', 'LIFECYCLE');
    
    // Clean up old artifacts before starting
    try { if (cleanup && typeof cleanup.run === 'function') cleanup.run(); } catch (e) { console.error('[Cleanup] Failed:', e.message); }

    const args = process.argv.slice(2);
    
    // 1. Force Feishu Card Reporting
    process.env.EVOLVE_REPORT_TOOL = 'feishu-card';
    
    // 2. Resolve Core Evolver Path
    const possibleDirs = ['../private-evolver', '../evolver', '../capability-evolver'];
    let evolverDir = null;
    
    for (const d of possibleDirs) {
        const fullPath = path.resolve(__dirname, d);
        if (fs.existsSync(fullPath)) {
            evolverDir = fullPath;
            break;
        }
    }
    
    if (!evolverDir) {
        console.error("Critical Error: Core 'evolver' plugin not found in ../private-evolver, ../evolver, or ../capability-evolver!");
        process.exit(1);
    }

    const mainScript = path.join(evolverDir, 'index.js');
    const lifecycleLog = path.resolve(__dirname, '../../logs/wrapper_lifecycle.log');
    
    const MAX_RETRIES = 5;
    const isLoop = args.includes('--loop');
    const loopSleepSeconds = Number.parseInt(process.env.EVOLVE_WRAPPER_LOOP_SLEEP_SECONDS || '2', 10);
    const loopFailBackoffSeconds = Number.parseInt(process.env.EVOLVE_WRAPPER_FAIL_BACKOFF_SECONDS || '30', 10);
    const loopMaxCycles = Number.parseInt(process.env.EVOLVE_WRAPPER_MAX_CYCLES || '0', 10); // 0 = unlimited
    
    if (!fs.existsSync(path.dirname(lifecycleLog))) {
        fs.mkdirSync(path.dirname(lifecycleLog), { recursive: true });
    }

    const cycleFile = path.resolve(path.dirname(lifecycleLog), 'cycle_count.txt');

    let childArgsArrBase = args.filter(a => a !== '--once' && a !== '--loop' && a !== '--mad-dog');
    if (childArgsArrBase.length === 0) {
        childArgsArrBase = ['run'];
    }

    let cycleCount = 0;
    while (true) {
        checkKillSwitch(); // Feature 1

        if (loopMaxCycles > 0 && cycleCount >= loopMaxCycles) {
            console.log(`Reached max cycles (${loopMaxCycles}). Exiting.`);
            return;
        }
        cycleCount++;

        const cycleTag = nextCycleTag(cycleFile);

        // Feature 4: Injection
        const injectedHint = getInjectionHint();
        if (injectedHint) {
            process.env.EVOLVE_HINT = injectedHint;
            sendCardInternal(`🧠 **Thought Injected:**\n"${injectedHint}"`, 'INFO');
        } else {
            delete process.env.EVOLVE_HINT;
        }

        const targetArg = process.env.EVOLVE_TARGET ? ` --target "${process.env.EVOLVE_TARGET}"` : '';
        process.env.EVOLVE_REPORT_DIRECTIVE = `3.  **REPORT (FEISHU WRAPPER)**:
    - You MUST use the \`feishu-evolver-wrapper/report.js\` tool.
    - The report MUST have a colored header to distinguish it from rich text.
    - Command:
      \`\`\`bash
      node skills/feishu-evolver-wrapper/report.js --cycle "Cycle #${cycleTag}" --title "🧬 Evolution #${cycleTag}" --status "Status: [WRAPPED] Step Complete."${targetArg}
      \`\`\`
    - Target: Auto-detects context (Evolution group or master) unless overridden.`;

        if (isLoop) {
            process.env.EVOLVE_EXTRA_MODES = `- Mode B (Wrapper Loop):
      - You are running under a wrapper-managed continuous loop.
      - Action: Perform ONE evolution cycle, then exit cleanly.
      - Do NOT call sessions_spawn. Do NOT try to self-schedule.
      - The wrapper handles cycling, reporting delivery, and git sync.`;
        } else {
            process.env.EVOLVE_EXTRA_MODES = `- Mode A (Atomic/Cron):
      - Do NOT call sessions_spawn.
      - Goal: Complete ONE generation, update state, and exit gracefully.`;
        }

        let attempts = 0;
        let ok = false;
        while (attempts < MAX_RETRIES && !ok) {
            attempts++;
            const startTime = Date.now();
            sessionLogs = { infoCount: 0, errorCount: 0, startTime, errors: [] }; // Reset logs

            fs.appendFileSync(
                lifecycleLog,
                `🧬 [${new Date(startTime).toISOString()}] START Wrapper PID=${process.pid} Attempt=${attempts} Cycle=#${cycleTag}\n`
            );

            try {
                const childArgs = childArgsArrBase.join(' ');
                console.log(`Delegating to Core (Attempt ${attempts}) Cycle #${cycleTag}: ${mainScript}`);
                forwardLogToFeishu(`🧬 Cycle #${cycleTag} started (Attempt ${attempts})`, 'LIFECYCLE');
                
                await new Promise((resolve, reject) => {
                    const child = spawn('node', [mainScript, ...childArgsArrBase], {
                        env: process.env,
                        stdio: ['ignore', 'pipe', 'pipe']
                    });

                    let fullStdout = '';

                    child.stdout.on('data', (data) => {
                        const str = data.toString();
                        process.stdout.write(str);
                        fullStdout += str;
                        forwardLogToFeishu(str, 'INFO');
                    });

                    child.stderr.on('data', (data) => {
                        const str = data.toString();
                        process.stderr.write(str);
                        forwardLogToFeishu(str, 'ERROR');
                    });

                    child.on('close', async (code) => {
                        try {
                            if (code !== 0) {
                                const err = new Error(`Child process exited with code ${code}`);
                                reject(err);
                                return;
                            }

                            if (fullStdout && fullStdout.includes('sessions_spawn({')) {
                                console.log('[Wrapper] Detected sessions_spawn request. Bridging to OpenClaw CLI...');
                                // [FIX 2026-02-08] Use JSON.parse instead of fragile regex.
                                // evolve.js bridge outputs valid JSON via JSON.stringify.
                                // Use lastIndexOf to target the LAST sessions_spawn (bridge output is always at the end).
                                // Match the BRIDGE output specifically: sessions_spawn({"
                                // The bridge uses JSON.stringify so keys are quoted: {"task":...}
                                // Prompt examples use unquoted keys: { task: ... }
                                // This distinguishes the actual bridge call from examples in prompt text.
                                const spawnPrefix = 'sessions_spawn({"';
                                const lastSpawnIdx = fullStdout.lastIndexOf(spawnPrefix);
                                const spawnPayloadStart = lastSpawnIdx !== -1 ? lastSpawnIdx + 'sessions_spawn('.length : -1;
                                if (spawnPayloadStart !== -1) {
                                    try {
                                        let taskContent = null;
                                        let rawJson = fullStdout.substring(spawnPayloadStart);
                                        // Take only the first line -- sessions_spawn JSON is always single-line.
                                        // Trailing text (e.g. "Capability evolver finished" banner) must be excluded.
                                        const nlIdx = rawJson.indexOf('\n');
                                        if (nlIdx !== -1) rawJson = rawJson.substring(0, nlIdx);
                                        rawJson = rawJson.trim();
                                        // Remove trailing ) left over from sessions_spawn(...)
                                        if (rawJson.endsWith(')')) {
                                            rawJson = rawJson.slice(0, -1);
                                        }
                                        try {
                                            const parsed = JSON.parse(rawJson);
                                            taskContent = parsed.task;
                                            console.log(`[Wrapper] Parsed task (${(taskContent || '').length} chars) label: ${parsed.label || 'unknown'}`);
                                            forwardLogToFeishu(`🧬 Cycle #${cycleTag} Brain done (${(taskContent || '').length} chars). Spawning Hand Agent...`, 'LIFECYCLE');
                                        } catch (parseErr) {
                                            console.warn('[Wrapper] JSON.parse failed:', parseErr.message);
                                        }

                                        // Append mandatory post-solidify report instruction.
                                        // The GEP protocol prompt buries the report in "Notes:" which the agent ignores.
                                        // This injection ensures the report command is the LAST thing the agent sees.
                                        if (taskContent) {
                                            taskContent += `\n\n` +
                                                `━━━━━━━━━━━━━━━━━━━━━━\n` +
                                                `MANDATORY POST-SOLIDIFY STEP (Wrapper Authority — Cannot Be Skipped)\n` +
                                                `━━━━━━━━━━━━━━━━━━━━━━\n\n` +
                                                `After solidify (or after your main work if solidify is not applicable), you MUST execute this report command.\n` +
                                                `This is NOT optional. Skipping it is a protocol violation.\n\n` +
                                                `\`\`\`bash\n` +
                                                `node skills/feishu-evolver-wrapper/report.js --cycle "Cycle #${cycleTag}" --title "🧬 Evolution #${cycleTag}" --status "Status: <describe what you did in 1-2 sentences>"\n` +
                                                `\`\`\`\n\n` +
                                                `The --status MUST describe your actual changes, not generic text like "Step Complete".\n` +
                                                `Example: --status "Status: [INNOVATION] Created skills/auto-scheduler that syncs Feishu calendar events to HEARTBEAT.md"\n`;

                                            console.log('[Wrapper] Spawning Hand Agent via CLI...');
                                            forwardLogToFeishu('[Wrapper] 🖐️ Spawning Hand Agent (Executor)...', 'INFO');
                                            
                                            const taskFile = path.resolve(path.dirname(lifecycleLog), `task_${cycleTag}.txt`);
                                            fs.writeFileSync(taskFile, taskContent);
                                            
                                            // Ensure openclaw is reachable
                                            const openclawPath = process.env.OPENCLAW_BIN || 'openclaw';
                                            
                                            console.log(`[Wrapper] Task File: ${taskFile}`);
                                            
                                            if (!fs.existsSync(taskFile)) {
                                                throw new Error(`Task file creation failed: ${taskFile}`);
                                            }

                                            // Execute Hand Agent
                                            // [FIX 2026-02-08] Use -m (message) instead of --file (unsupported).
                                            // Use --session-id with a unique ID to isolate evolver cycles from the main session.
                                            const sessionId = `evolver_hand_${cycleTag}_${Date.now()}`;
                                            await new Promise((resolveHand, rejectHand) => {
                                                console.log(`[Wrapper] Executing: ${openclawPath} agent --agent main --session-id ${sessionId} -m <task> --timeout 600`);
                                                const handChild = spawn(openclawPath, ['agent', '--agent', 'main', '--session-id', sessionId, '-m', taskContent, '--timeout', '600'], {
                                                    env: { ...process.env },
                                                    stdio: ['ignore', 'pipe', 'pipe'] // Pipe stdio to capture logs
                                                });

                                                handChild.stdout.on('data', (d) => {
                                                    const s = d.toString();
                                                    process.stdout.write(`[Hand] ${s}`);
                                                    // forwardLogToFeishu(`[Hand] ${s}`, 'INFO'); // verbose?
                                                });

                                                handChild.stderr.on('data', (d) => {
                                                    const s = d.toString();
                                                    process.stderr.write(`[Hand ERR] ${s}`);
                                                    forwardLogToFeishu(`[Hand ERR] ${s}`, 'ERROR');
                                                });

                                                handChild.on('error', (err) => {
                                                    console.error(`[Wrapper] Hand Agent spawn error: ${err.message}`);
                                                    forwardLogToFeishu(`[Wrapper] Hand Agent spawn error: ${err.message}`, 'ERROR');
                                                    rejectHand(err);
                                                });

                                                handChild.on('close', (handCode) => {
                                                    if (handCode === 0) {
                                                        console.log('[Wrapper] Hand Agent finished successfully.');
                                                        forwardLogToFeishu(`🧬 Cycle #${cycleTag} Hand Agent completed successfully.`, 'LIFECYCLE');
                                                        resolveHand();
                                                    } else {
                                                        const msg = `[Wrapper] Hand Agent failed with code ${handCode}`;
                                                        forwardLogToFeishu(`🧬 Cycle #${cycleTag} Hand Agent failed (code ${handCode})`, 'LIFECYCLE');
                                                        console.error(msg);
                                                        forwardLogToFeishu(msg, 'ERROR');
                                                        // We resolve instead of reject to allow the cycle to complete "successfully" 
                                                        // (the brain worked, the hand failed)
                                                        // But let's log it clearly.
                                                        resolveHand(); 
                                                    }
                                                });
                                            });

                                        } else {
                                            console.warn('[Wrapper] Could not extract task content from sessions_spawn');
                                        }
                                    } catch (err) {
                                        console.error('[Wrapper] Bridge execution failed:', err.message);
                                        forwardLogToFeishu(`[Wrapper] Bridge execution failed: ${err.message}`, 'ERROR');
                                    }
                                }
                            }
                            resolve(); // Resolve the main cycle promise
                        } catch (e) {
                            reject(e);
                        }
                    });

                    child.on('error', (err) => {
                        reject(err);
                    });
                });

                const duration = ((Date.now() - startTime) / 1000).toFixed(2);
                fs.appendFileSync(
                    lifecycleLog,
                    `🧬 [${new Date().toISOString()}] SUCCESS Wrapper PID=${process.pid} Cycle=#${cycleTag} Duration=${duration}s\n`
                );
                console.log('Wrapper proxy complete.');
                forwardLogToFeishu(`🧬 Cycle #${cycleTag} complete (${duration}s)`, 'LIFECYCLE');
                
                // Feature 5: Git Sync (Safety Net)
                gitSync();

                // Feature 7: Issue Tracker (record problems to Feishu doc)
                try {
                    if (issueTracker && typeof issueTracker.recordIssues === 'function') {
                        // Extract signals from the task file for this cycle
                        const taskFile = path.resolve(path.dirname(lifecycleLog), `task_${cycleTag}.txt`);
                        let signals = [];
                        try {
                            const taskContent = fs.readFileSync(taskFile, 'utf8');
                            const sigMatch = taskContent.match(/Context \[Signals\]:\s*\n(\[.*?\])/);
                            if (sigMatch) signals = JSON.parse(sigMatch[1]);
                        } catch (_) {}
                        issueTracker.recordIssues(signals, cycleTag, '').catch(e =>
                            console.error('[IssueTracker] Error:', e.message)
                        );
                    }
                } catch (e) {
                    console.error('[IssueTracker] Error:', e.message);
                }
                
                sendSummary(cycleTag, duration, true); // Feature 2
                
                // Feature 8: Mirror report to CN group (exact same format, same report.js)
                try {
                    const reportScript = path.resolve(__dirname, 'report.js');
                    if (fs.existsSync(reportScript) && FEISHU_CN_REPORT_GROUP) {
                        execSync(`node "${reportScript}" --cycle "Cycle #${cycleTag}" --title "🧬 Evolution #${cycleTag}" --status "Status: [WRAPPED] Step Complete." --target "${FEISHU_CN_REPORT_GROUP}"`, {
                            timeout: 15000, stdio: 'ignore', env: process.env
                        });
                    }
                } catch (e) {
                    console.error('[CN Report] Failed:', e.message);
                }

                ok = true;
            } catch (e) {
                const duration = ((Date.now() - startTime) / 1000).toFixed(2);
                fs.appendFileSync(
                    lifecycleLog,
                    `🧬 [${new Date().toISOString()}] ERROR Wrapper PID=${process.pid} Cycle=#${cycleTag} Duration=${duration}s: ${e.message}\n`
                );
                console.error(`Wrapper proxy failed (Attempt ${attempts}) Cycle #${cycleTag}:`, e.message);
                
                // On failure, we might send a summary OR let the real-time errors speak for themselves.
                // Sending a FAILURE summary is good practice.
                sendSummary(cycleTag, duration, false); 

                if (attempts < MAX_RETRIES) {
                    const delay = Math.min(60, 5 * attempts);
                    console.log(`Retrying in ${delay} seconds...`);
                    sleepSeconds(delay);
                }
            }
        }

        if (!ok) {
            console.error('Wrapper failed after max retries.');
            if (!isLoop) process.exit(1);
            console.log(`Backoff ${loopFailBackoffSeconds}s before next cycle...`);
            sleepSeconds(loopFailBackoffSeconds);
        }

        if (!isLoop) return;

        fs.appendFileSync(
            lifecycleLog,
            `🧬 [${new Date().toISOString()}] SLEEP Wrapper PID=${process.pid} NextCycleIn=${loopSleepSeconds}s\n`
        );
        sleepSeconds(loopSleepSeconds);
    }
}

run();
