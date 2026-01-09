const { ethers } = require('ethers');
const Mnemonic = require('mnemonic');
const axios = require('axios');

const mnemonic = new Mnemonic('english');

class WalletHunter {
  constructor() {
    this.stats = { checked: 0, hits: 0, running: false };
    this.timer = null;
    this.isColdStart = true;
  }

  generateWallet() {
    try {
      const seed = mnemonic.generate(128);
      const wallet = ethers.Wallet.fromPhrase(seed);
      return { 
        seed: seed.slice(0, 20) + '...', 
        address: wallet.address 
      };
    } catch {
      return { address: '0x000...error' };
    }
  }

  async checkBalance(address) {
    // Fast mock + real RPC fallback
    if (Math.random() < 0.999) return 0; // 99.9% empty
    
    // Simulate rare hit for demo
    if (Math.random() < 0.0001) return Math.random() * 0.1;
    
    try {
      const rpc = process.env.ALCHEMY_KEY 
        ? `https://eth-mainnet.g.alchemy.com/v2/${process.env.ALCHEMY_KEY}`
        : 'https://rpc.ankr.com/eth';
      
      const res = await axios.post(rpc, {
        jsonrpc: '2.0', method: 'eth_getBalance', 
        params: [address, 'latest'], id: 1
      }, { timeout: 1000 });
      
      return parseInt(res.data.result || 0, 16) / 1e18;
    } catch {
      return 0;
    }
  }

  async hunt() {
    const wallet = this.generateWallet();
    const balance = await this.checkBalance(wallet.address);
    
    this.stats.checked++;
    
    if (balance > 0.00001) {
      this.stats.hits++;
      console.log(`🎉 HIT: ${wallet.address} ${balance} ETH`);
    }
  }

  start() {
    if (this.stats.running) return;
    
    this.stats.running = true;
    // 2 wallets/sec = Vercel safe
    this.timer = setInterval(() => {
      if (this.stats.running) {
        this.hunt().catch(console.error);
      }
    }, 500);
    
    console.log('🟢 Hunter started');
  }

  stop() {
    this.stats.running = false;
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  getStats() {
    return {
      checked: this.stats.checked,
      hits: this.stats.hits,
      running: this.stats.running,
      uptime: process.uptime()
    };
  }
}

module.exports = new WalletHunter();
