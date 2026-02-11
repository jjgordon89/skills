const fs = require('fs');
const path = require('path');

// --- Configuration ---
const DB_PATH = path.resolve(__dirname, '../../memory/user_registry.json');

// --- Helpers ---
function loadDB() {
    if (!fs.existsSync(DB_PATH)) return {};
    try {
        return JSON.parse(fs.readFileSync(DB_PATH, 'utf8'));
    } catch (e) {
        console.error("Error reading DB:", e.message);
        return {};
    }
}

// --- Main ---
const query = process.argv[2];
if (!query) {
    console.error("Usage: node skills/identity-manager/search.js <query>");
    process.exit(1);
}

const db = loadDB();
const results = [];

for (const id in db) {
    const user = db[id];
    const nameMatch = user.name && user.name.toLowerCase().includes(query.toLowerCase());
    const aliasMatch = user.alias && user.alias.toLowerCase().includes(query.toLowerCase());
    
    if (nameMatch || aliasMatch) {
        results.push({
            Name: user.name,
            Role: user.role || '-',
            Alias: user.alias || '-',
            ID: user.id
        });
    }
}

if (results.length > 0) {
    console.table(results);
} else {
    console.log(`No users found matching "${query}".`);
    console.log(`Try updating the registry with: node skills/identity-manager/sync.js`);
}