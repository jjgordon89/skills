const fs = require('fs');
const path = require('path');
const { fetchWithAuth } = require('../common/feishu-client');

// --- Configuration ---
const DB_PATH = path.resolve(__dirname, '../../memory/user_registry.json');
const PAGE_SIZE = 50; // Feishu max 100

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

function saveDB(data) {
    fs.writeFileSync(DB_PATH, JSON.stringify(data, null, 2));
}

// --- API Logic ---

// 1. Get List of Chats the Bot is in
async function getChats() {
    let chats = [];
    let pageToken = '';
    
    do {
        const url = `https://open.feishu.cn/open-apis/im/v1/chats?page_size=${PAGE_SIZE}&page_token=${pageToken}`;
        const res = await fetchWithAuth(url);
        const json = await res.json();
        
        if (json.code !== 0) {
            console.error(`Failed to list chats: ${json.msg}`);
            break;
        }
        
        if (json.data && json.data.items) {
            chats = chats.concat(json.data.items);
        }
        
        pageToken = json.data.has_more ? json.data.page_token : '';
    } while (pageToken);
    
    return chats;
}

// 2. Get Members of a Chat
async function getMembers(chatId) {
    let members = [];
    let pageToken = '';

    do {
        const url = `https://open.feishu.cn/open-apis/im/v1/chats/${chatId}/members?page_size=${PAGE_SIZE}&page_token=${pageToken}`;
        const res = await fetchWithAuth(url);
        const json = await res.json();
        
        if (json.code !== 0) {
            // Some chats might restrict member listing
            // console.warn(`Failed to list members for ${chatId}: ${json.msg}`);
            break;
        }
        
        if (json.data && json.data.items) {
            members = members.concat(json.data.items);
        }
        
        pageToken = json.data.has_more ? json.data.page_token : '';
    } while (pageToken);
    
    return members;
}

// --- Main Sync Logic ---
async function sync() {
    console.log("🔄 Starting Identity Sync...");
    
    // 1. Fetch Chats
    const chats = await getChats();
    console.log(`✅ Found ${chats.length} chats.`);
    
    // 2. Load DB
    const db = loadDB();
    let newCount = 0;
    let updateCount = 0;
    
    // 3. Iterate Chats
    for (const chat of chats) {
        // console.log(`  > Scanning ${chat.name || 'Unnamed Group'} (${chat.chat_id})...`);
        const members = await getMembers(chat.chat_id);
        // console.log(`    - Members count: ${members.length}`); // Debug
        
        for (const m of members) {
            // console.log("Member:", m); // Debug
            // Feishu returns: member_id (depends on query), open_id (always present for users), union_id (if requested)
            // But we want to use open_id as the primary key if possible, or fall back to whatever is available.
            // Actually, for sending messages, open_id is best.
            
            const realId = m.open_id || m.member_id || m.union_id || m.user_id;
            const name = m.name || m.alias || (m.member_id === process.env.FEISHU_APP_ID ? "Bot" : "Unknown");
            
            if (!realId || !name) continue;
            
            if (!db[realId]) {
                db[realId] = {
                    id: realId,
                    name: name,
                    role: "User (Auto-Sync)",
                    alias: "",
                    firstSeen: new Date().toISOString(),
                    source: chat.name
                };
                newCount++;
                console.log(`    🆕 Found: ${name} (${realId})`);
            } else {
                // Update name if changed
                if (db[realId].name !== name) {
                    db[realId].name = name;
                    db[realId].updatedAt = new Date().toISOString();
                    updateCount++;
                }
            }
        }
    }
    
    saveDB(db);
    console.log(`\n🎉 Sync Complete. Added ${newCount} users, Updated ${updateCount} users.`);
}

sync().catch(console.error);
