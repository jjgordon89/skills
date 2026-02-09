const { fetchWithAuth } = require('../common/feishu-client.js');

async function sendCard({ target, title, text, color }) {
    if (!target) {
        throw new Error("Target ID is required");
    }

    const receiveIdType = target.startsWith('oc_') ? 'chat_id' : 'open_id';

    const card = {
        config: { wide_screen_mode: true },
        header: {
            title: { tag: 'plain_text', content: title || 'Log' },
            template: color || 'blue'
        },
        elements: [
            {
                tag: 'div',
                text: {
                    tag: 'lark_md',
                    content: text
                }
            },
            {
                tag: 'note',
                elements: [
                    { tag: 'plain_text', content: `PID: ${process.pid}` }
                ]
            }
        ]
    };

    const payload = {
        receive_id: target,
        msg_type: 'interactive',
        content: JSON.stringify(card)
    };

    const res = await fetchWithAuth(`https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=${receiveIdType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (data.code !== 0) {
        throw new Error(`Feishu API Error: ${data.msg}`);
    }
    return data;
}

module.exports = { sendCard };
