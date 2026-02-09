const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// SKILLS MONITOR
// Proactively checks all installed skills for syntax errors and missing dependencies.

const SKILLS_DIR = path.resolve(__dirname, '../../skills');

function checkSkill(skillName) {
    const skillPath = path.join(SKILLS_DIR, skillName);
    const issues = [];
    
    if (!fs.statSync(skillPath).isDirectory()) return null;

    // 1. Check Mandatory Files
    if (!fs.existsSync(path.join(skillPath, 'SKILL.md'))) {
        issues.push('Missing SKILL.md');
    }
    
    // 2. Check Syntax of Main Entry Point
    // Heuristic: index.js or main in package.json
    let mainFile = 'index.js';
    if (fs.existsSync(path.join(skillPath, 'package.json'))) {
        try {
            const pkg = JSON.parse(fs.readFileSync(path.join(skillPath, 'package.json'), 'utf8'));
            if (pkg.main) mainFile = pkg.main;
        } catch (e) {
            issues.push('Invalid package.json');
        }
    }

    const entryPoint = path.join(skillPath, mainFile);
    if (fs.existsSync(entryPoint)) {
        try {
            execSync(`node -c "${entryPoint}"`, { stdio: 'ignore' });
        } catch (e) {
            issues.push(`Syntax Error in ${mainFile}`);
        }
    } else {
        // Not all skills have index.js (some are just markdown or tools)
        // Check if there are ANY .js files
        const hasJs = fs.readdirSync(skillPath).some(f => f.endsWith('.js'));
        if (hasJs && mainFile === 'index.js') {
             // If JS exists but index.js missing and no package.json override, might be an issue?
             // Or maybe it's a multi-tool skill.
        }
    }

    if (issues.length > 0) {
        return { name: skillName, issues };
    }
    return null;
}

function run() {
    console.log('[SkillsMonitor] scanning...');
    const skills = fs.readdirSync(SKILLS_DIR);
    const report = [];

    for (const skill of skills) {
        if (skill.startsWith('.')) continue; // skip hidden
        const result = checkSkill(skill);
        if (result) report.push(result);
    }

    if (report.length > 0) {
        console.log(`[SkillsMonitor] Found issues in ${report.length} skills.`);
        report.forEach(r => {
            console.log(`- ${r.name}: ${r.issues.join(', ')}`);
        });
        
        // Return report for upstream usage
        return report;
    } else {
        console.log('[SkillsMonitor] All skills syntax OK.');
        return [];
    }
}

if (require.main === module) {
    const issues = run();
    if (issues.length > 0) {
        process.exit(1);
    }
}

module.exports = { run };
