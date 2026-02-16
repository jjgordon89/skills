/**
 * OpenClaw Solana Connect - Test Suite v2.0
 */

const { generateWallet, connectWallet, getBalance, getTransactions, getTokenAccounts, getConnection, isTestNet, airdrop } = require('./scripts/solana.js');

console.log('🧪 OpenClaw Solana Connect v2.0 - Test Suite\n');

let passed = 0;
let failed = 0;

// Test 1: Generate new wallet
function test1() {
  console.log('Test 1: Generate new wallet...');
  try {
    const wallet = generateWallet();
    // SECURITY: Private key is NOT returned anymore - only address
    if (wallet.address && wallet.address.length > 30) {
      console.log(`  ✅ PASSED - Address: ${wallet.address.slice(0,8)}... (private key protected)`);
      passed++;
    } else {
      console.log('  ❌ FAILED - Invalid address');
      failed++;
    }
  } catch (e) {
    console.log(`  ❌ FAILED - ${e.message}`);
    failed++;
  }
}

// Test 2: Connect to RPC
async function test2() {
  console.log('Test 2: Connect to Solana RPC...');
  try {
    const rpc = getConnection();
    const version = await rpc.getVersion().send();
    console.log(`  ✅ PASSED - RPC connected, version: ${version.solanaCore}`);
    passed++;
  } catch (e) {
    console.log(`  ❌ FAILED - ${e.message}`);
    failed++;
  }
}

// Test 3: Get balance
async function test3() {
  console.log('Test 3: Get balance for known address...');
  try {
    const testAddr = 'GeD4JLVBYCGYGV3dnrVRvCjKC2X4wCJMxRDrgMHTJpH';
    const balance = await getBalance(testAddr);
    console.log(`  ✅ PASSED - Balance: ${balance.sol} SOL`);
    passed++;
  } catch (e) {
    console.log(`  ❌ FAILED - ${e.message}`);
    failed++;
  }
}

// Test 4: Get token accounts
async function test4() {
  console.log('Test 4: Get token accounts...');
  try {
    const testAddr = 'GeD4JLVBYCGYGV3dnrVRvCjKC2X4wCJMxRDrgMHTJpH';
    const tokens = await getTokenAccounts(testAddr);
    console.log(`  ✅ PASSED - Found ${tokens.length} token accounts`);
    passed++;
  } catch (e) {
    console.log(`  ❌ FAILED - ${e.message}`);
    failed++;
  }
}

// Test 5: Get transactions
async function test5() {
  console.log('Test 5: Get recent transactions...');
  try {
    const testAddr = 'GeD4JLVBYCGYGV3dnrVRvCjKC2X4wCJMxRDrgMHTJpH';
    const txs = await getTransactions(testAddr, 3);
    console.log(`  ✅ PASSED - Found ${txs.length} transactions`);
    passed++;
  } catch (e) {
    console.log(`  ❌ FAILED - ${e.message}`);
    failed++;
  }
}

// Test 6: Connect wallet with private key
function test6() {
  console.log('Test 6: Connect wallet with private key...');
  try {
    const privateKey = '6fDauV66K8RDW3NjgTiDuB2cVNRRLV3wQ8CC3tzN43LP'; // From test 1
    const wallet = connectWallet(privateKey);
    if (wallet.address && wallet.address.length > 30) {
      console.log(`  ✅ PASSED - Address: ${wallet.address.slice(0,8)}...`);
      passed++;
    } else {
      console.log('  ❌ FAILED - Invalid address');
      failed++;
    }
  } catch (e) {
    console.log(`  ❌ FAILED - ${e.message}`);
    failed++;
  }
}

// Run tests
(async () => {
  test1();
  await test2();
  await test3();
  await test4();
  await test5();
  test6();
  
  console.log('\n========================================');
  console.log(`📊 Results: ${passed} passed, ${failed} failed`);
  console.log('========================================\n');
  
  if (failed > 0) {
    console.log('⚠️  Some tests failed. Check errors above.');
    process.exit(1);
  } else {
    console.log('🎉 All tests passed!\n');
    process.exit(0);
  }
})();
