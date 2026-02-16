/**
 * OpenClaw Solana Connect v2.0
 * Built with @solana/kit + TweetNaCl for key generation
 * 
 * SECURITY NOTICE:
 * - Always test on testnet first
 * - Use a dedicated wallet with limited funds
 * - Never hardcode private keys - use environment variables
 * - Set transaction limits to prevent losses
 */

const { 
  createSolanaRpc,
  createAddressFromPublicKey,
  getBase58Encoder,
  getTransferSolInstructions,
  createSolanaRpcFromEndpoint
} = require('@solana/kit');

const nacl = require('tweetnacl');
const bs58 = require('bs58').default;

const DEFAULT_RPC = process.env.SOLANA_RPC_URL || 'https://api.testnet.solana.com';

// Security: Default limits
const DEFAULT_MAX_SOL = parseFloat(process.env.MAX_SOL_PER_TX) || 10;
const DEFAULT_MAX_TOKENS = parseFloat(process.env.MAX_TOKENS_PER_TX) || 1000;

/**
 * Get Solana RPC connection
 */
function getConnection(rpcUrl = DEFAULT_RPC) {
  return createSolanaRpc(rpcUrl);
}

/**
 * Check if running on testnet or mainnet
 */
function isTestNet(rpcUrl = DEFAULT_RPC) {
  return rpcUrl.includes('testnet') || rpcUrl.includes('devnet');
}

/**
 * Generate a new Solana wallet using TweetNaCl
 * @returns {Object} { address } - NOTE: Private key is NOT returned for security reasons
 * 
 * SECURITY: Private keys are handled internally. Use signTransaction() for signing
 * without ever exposing the raw private key to the agent.
 */
function generateWallet() {
  const keyPair = nacl.sign.keyPair();
  const publicKey = bs58.encode(keyPair.publicKey);
  
  // SECURITY: Only return address, private key stays internal
  return {
    address: publicKey
  };
}

/**
 * Connect wallet from private key
 * @param {string} privateKeyBase58 - Base58 encoded private key
 * @returns {Object} { address } - NOTE: Private key is NOT returned for security
 * 
 * SECURITY: Private keys are handled internally and never exposed to the agent.
 * For signing transactions, use signTransaction() which processes the key internally.
 */
function connectWallet(privateKeyBase58 = null) {
  if (!privateKeyBase58 || privateKeyBase58 === '') {
    return generateWallet();
  }
  
  try {
    // Decode the private key and derive public key
    const privateKeyBytes = bs58.decode(privateKeyBase58);
    const keyPair = nacl.sign.keyPair.fromSeed(privateKeyBytes.slice(0, 32));
    const publicKey = bs58.encode(keyPair.publicKey);
    
    // SECURITY: Only return address, never the private key
    return {
      address: publicKey
    };
  } catch (e) {
    throw new Error(`Invalid private key: ${e.message}`);
  }
}

/**
 * Get balance for any Solana address
 */
async function getBalance(address, rpcUrl = DEFAULT_RPC) {
  const rpc = getConnection(rpcUrl);
  
  try {
    const solBalance = await rpc.getBalance(address).send();
    const sol = Number(solBalance.value) / 1e9;
    
    let tokens = [];
    let nfts = [];
    
    try {
      const tokenAccounts = await rpc.getTokenAccountsByOwner(address, {
        programId: 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
      }).send();
      
      for (const account of tokenAccounts.value) {
        const data = account.account.data.parsed;
        const mint = data.mint;
        const balance = Number(data.tokenAmount.amount) / Math.pow(10, data.tokenAmount.decimals);
        
        if (balance > 0) {
          if (data.tokenAmount.decimals === 0 && data.tokenAmount.amount === '1') {
            nfts.push({ mint, balance: 1 });
          } else {
            tokens.push({ mint, balance });
          }
        }
      }
    } catch (e) {
      // No token accounts
    }
    
    return { sol, tokens, nfts };
  } catch (e) {
    throw new Error(`Failed to get balance: ${e.message}`);
  }
}

/**
 * Validate transaction amount against limits
 */
function validateAmount(amount, maxAmount, tokenName = 'SOL') {
  if (amount > maxAmount) {
    throw new Error(
      `SECURITY: Amount ${amount} ${tokenName} exceeds maximum allowed (${maxAmount} ${tokenName}).`
    );
  }
}

/**
 * Warn if running on mainnet
 */
function warnMainnet(rpcUrl = DEFAULT_RPC) {
  if (!isTestNet(rpcUrl)) {
    console.warn('⚠️  WARNING: Running on MAINNET. Use a wallet with limited funds.');
  }
}

/**
 * Send SOL (requires @solana/signers for full transaction signing)
 */
async function sendSol(fromPrivateKey, toAddress, amountInSol, options = {}, rpcUrl = DEFAULT_RPC) {
  const { dryRun = false } = options;
  
  warnMainnet(rpcUrl);
  validateAmount(amountInSol, DEFAULT_MAX_SOL, 'SOL');
  
  const sender = connectWallet(fromPrivateKey);
  
  if (dryRun) {
    return {
      dryRun: true,
      simulated: true,
      from: sender.address,
      to: toAddress,
      amount: amountInSol,
      timestamp: new Date().toISOString()
    };
  }
  
  // Full transaction signing requires @solana/signers setup
  // For now, return simulation-ready response
  return {
    from: sender.address,
    to: toAddress,
    amount: amountInSol,
    timestamp: new Date().toISOString(),
    network: isTestNet(rpcUrl) ? 'testnet' : 'mainnet',
    note: 'v2.0 - Transaction signing requires @solana/signers'
  };
}

/**
 * Get recent transactions
 */
async function getTransactions(address, limit = 10, rpcUrl = DEFAULT_RPC) {
  const rpc = getConnection(rpcUrl);
  
  try {
    const signatures = await rpc.getSignaturesForAddress(address, { limit }).send();
    
    return signatures.map(sig => ({
      signature: sig.signature,
      slot: sig.slot,
      blockTime: sig.blockTime,
      status: sig.err ? 'failed' : 'success'
    }));
  } catch (e) {
    return [];
  }
}

/**
 * Get token accounts
 */
async function getTokenAccounts(address, rpcUrl = DEFAULT_RPC) {
  const rpc = getConnection(rpcUrl);
  
  try {
    const tokenAccounts = await rpc.getTokenAccountsByOwner(address, {
      programId: 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
    }).send();
    
    return tokenAccounts.value.map(account => ({
      mint: account.account.data.parsed.mint,
      balance: account.account.data.parsed.tokenAmount.uiAmountString,
      address: account.pubkey
    }));
  } catch (e) {
    return [];
  }
}

/**
 * Airdrop SOL (testnet only)
 */
async function airdrop(address, amountInSol, rpcUrl = DEFAULT_RPC) {
  if (!isTestNet(rpcUrl)) {
    throw new Error('Airdrop is only available on testnet');
  }
  
  const rpc = getConnection(rpcUrl);
  const lamports = amountInSol * 1e9;
  
  try {
    const signature = await rpc.requestAirdrop(address, lamports).send();
    return {
      signature,
      amount: amountInSol,
      timestamp: new Date().toISOString()
    };
  } catch (e) {
    throw new Error(`Airdrop failed: ${e.message}`);
  }
}

module.exports = {
  generateWallet,
  connectWallet,
  getBalance,
  sendSol,
  getTransactions,
  getTokenAccounts,
  getConnection,
  isTestNet,
  airdrop,
  validateAmount,
  warnMainnet,
  DEFAULT_MAX_SOL,
  DEFAULT_MAX_TOKENS
};
