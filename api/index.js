const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Import with error handling
let hunter;
try {
  hunter = require('../wallet-hunter.js');
} catch (e) {
  console.error('Hunter init error:', e);
  hunter = { getStats: () => ({ checked: 0, hits: 0, running: false }) };
}

// Routes
app.get('/api/stats', (req, res) => {
  try {
    res.json(hunter.getStats());
  } catch (e) {
    res.status(500).json({ error: 'Stats error', checked: 0 });
  }
});

app.post('/api/hunt', (req, res) => {
  try {
    const { action } = req.body;
    if (action === 'start') hunter.start();
    if (action === 'stop') hunter.stop();
    res.json({ status: 'ok' });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: 'Hunt error' });
  }
});

app.get('/', (req, res) => {
  res.json({ status: '🚀 Wallet Hunter Live', uptime: new Date().toISOString() });
});

module.exports = app;
