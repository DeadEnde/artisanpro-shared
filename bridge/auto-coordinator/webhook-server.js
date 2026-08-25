/**
 * ArtisanPro Auto-Coordinator Webhook Server
 * 
 * Optionnel - Serveur li kay-sm3 l GitHub webhooks w kay-dir auto-assign f real-time
 * 
 * Usage:
 * 1. Deploy had server f Vercel / Railway / VPS
 * 2. Zid webhook f GitHub repo: Settings -> Webhooks -> Add webhook
 *    Payload URL: https://your-server.com/webhook
 *    Content type: application/json
 *    Events: Push
 * 3. Mli agent ydir push, GitHub y3ayet l had server, server ydir auto-assign w ypushi
 * 
 * Hadi alternative l GitHub Actions - ila bghiti control ktr
 */

const http = require('http');
const crypto = require('crypto');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Config
const PORT = process.env.PORT || 3000;
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'artisanpro-secret-2026';
const REPO_PATH = process.env.REPO_PATH || '/tmp/artisanpro-shared';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN || ''; // ghp_...

function log(msg) {
  console.log(`[${new Date().toISOString()}] ${msg}`);
}

function verifySignature(payload, signature) {
  if (!WEBHOOK_SECRET) return true; // Skip if no secret
  const hmac = crypto.createHmac('sha256', WEBHOOK_SECRET);
  hmac.update(payload);
  const expected = `sha256=${hmac.digest('hex')}`;
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

function runCoordinator() {
  try {
    log('Running auto-assign coordinator...');
    
    // Pull latest
    execSync('git pull origin main', { cwd: REPO_PATH, stdio: 'inherit' });
    
    // Run coordinator
    execSync('node scripts/auto-assign.js', { cwd: REPO_PATH, stdio: 'inherit' });
    
    // Check if changed
    const status = execSync('git status --porcelain', { cwd: REPO_PATH }).toString();
    if (status.trim()) {
      log('Changes detected, committing...');
      execSync('git config user.name "Auto-Coordinator Bot"', { cwd: REPO_PATH });
      execSync('git config user.email "bot@artisanpro.co"', { cwd: REPO_PATH });
      execSync('git add bridge/tasks.json bridge/locks.json bridge/state.json', { cwd: REPO_PATH });
      execSync(`git commit -m "auto: webhook triggered assignment ${new Date().toISOString()} [skip ci]"`, { cwd: REPO_PATH });
      
      // Push with token
      if (GITHUB_TOKEN) {
        const remote = execSync('git remote get-url origin', { cwd: REPO_PATH }).toString().trim();
        const authedRemote = remote.replace('https://', `https://${GITHUB_TOKEN}@`);
        execSync(`git push ${authedRemote} main`, { cwd: REPO_PATH });
        log('Pushed auto-assignments!');
      } else {
        execSync('git push origin main', { cwd: REPO_PATH });
      }
      return { changed: true, message: 'Auto-assigned and pushed' };
    } else {
      log('No changes needed');
      return { changed: false, message: 'No changes' };
    }
  } catch (e) {
    log(`Error in coordinator: ${e.message}`);
    return { changed: false, error: e.message };
  }
}

const server = http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/webhook') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      const signature = req.headers['x-hub-signature-256'] || '';
      
      // Verify
      if (WEBHOOK_SECRET && signature && !verifySignature(body, signature)) {
        log('Invalid signature!');
        res.writeHead(401);
        res.end('Invalid signature');
        return;
      }

      const payload = JSON.parse(body);
      const pusher = payload.pusher?.name || 'unknown';
      const commits = payload.commits?.length || 0;
      const branch = payload.ref?.split('/').pop() || 'unknown';

      log(`Webhook received: ${commits} commits to ${branch} by ${pusher}`);

      if (branch !== 'main') {
        res.writeHead(200);
        res.end('Ignored - not main branch');
        return;
      }

      // Run coordinator async
      setTimeout(() => {
        const result = runCoordinator();
        log(`Coordinator result: ${JSON.stringify(result)}`);
      }, 1000);

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', message: 'Coordinator triggered', pusher, commits }));
    });
  } else if (req.method === 'GET' && req.url === '/status') {
    // Status endpoint
    try {
      const tasks = JSON.parse(fs.readFileSync(path.join(REPO_PATH, 'bridge/tasks.json'), 'utf8'));
      const locks = JSON.parse(fs.readFileSync(path.join(REPO_PATH, 'bridge/locks.json'), 'utf8'));
      const state = JSON.parse(fs.readFileSync(path.join(REPO_PATH, 'bridge/state.json'), 'utf8'));
      
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'alive',
        tasks: tasks.tasks.map(t => ({ id: t.id, status: t.status, assignee: t.assignee, priority: t.priority })),
        locks: locks.locks,
        lastUpdate: state.lastUpdate,
        timestamp: new Date().toISOString()
      }, null, 2));
    } catch (e) {
      res.writeHead(500);
      res.end(JSON.stringify({ error: e.message }));
    }
  } else if (req.method === 'GET' && req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
      <h1>🤖 ArtisanPro Auto-Coordinator</h1>
      <p>Status: <b>Running</b></p>
      <p>Webhook: POST /webhook (GitHub push events)</p>
      <p>Status: GET /status (current tasks)</p>
      <p>Last check: ${new Date().toISOString()}</p>
      <hr>
      <p>How it works:</p>
      <ol>
        <li>Agent pushes to main</li>
        <li>GitHub calls /webhook</li>
        <li>Server pulls, runs auto-assign.js, checks dependencies</li>
        <li>If next tasks ready, assigns them and pushes</li>
        <li>New agents get notified via GitHub Issues</li>
      </ol>
      <p><a href="/status">View Status JSON</a></p>
    `);
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

server.listen(PORT, '0.0.0.0', () => {
  log(`Auto-Coordinator listening on port ${PORT}`);
  log(`Webhook: http://localhost:${PORT}/webhook`);
  log(`Status: http://localhost:${PORT}/status`);
});
