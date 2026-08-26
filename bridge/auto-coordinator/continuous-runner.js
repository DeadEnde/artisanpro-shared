#!/usr/bin/env node
// Continuous Auto-Coordinator Runner - Runs forever, checks every 60s
// Checks if AI agents work or not and gives them tasks recursively
// Lead Engineer + Shared Agent - 2026-08-25

const { execSync, spawnSync } = require('fs');
const fs = require('fs');
const path = require('path');

const REPO_PATH = path.join(__dirname, '../..');
const TASKS_PATH = path.join(REPO_PATH, 'bridge/tasks.json');
const LOCKS_PATH = path.join(REPO_PATH, 'bridge/locks.json');
const STATE_PATH = path.join(REPO_PATH, 'bridge/state.json');
const CHECK_INTERVAL_MS = 60 * 1000; // 1 minute

function log(msg) {
  const ts = new Date().toISOString();
  console.log(`[${ts}] ${msg}`);
}

function exec(cmd, opts = {}) {
  try {
    const out = require('child_process').execSync(cmd, { cwd: REPO_PATH, encoding: 'utf8', stdio: 'pipe', ...opts });
    return { ok: true, out: out.trim() };
  } catch (e) {
    return { ok: false, err: e.message, out: (e.stdout||'') + (e.stderr||'') };
  }
}

function loadJson(p) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (e) {
    return null;
  }
}

function runAutoAssign() {
  log('Running auto-assign.js...');
  const res = exec('node scripts/auto-assign.js');
  if (res.ok) {
    log(res.out.split('\n').slice(-10).join('\n'));
  } else {
    log(`auto-assign failed: ${res.err}\n${res.out}`);
  }
  return res.ok;
}

function checkAndPush() {
  const status = exec('git status --porcelain');
  if (!status.ok) {
    log(`git status failed: ${status.err}`);
    return false;
  }
  if (!status.out.trim()) {
    log('No changes to push');
    return false;
  }
  
  log(`Changes detected:\n${status.out}`);
  
  // Check diff
  const diff = exec('git diff --stat');
  log(`Diff stat:\n${diff.out}`);
  
  // Commit
  const commit = exec('git add bridge/tasks.json bridge/locks.json bridge/state.json && git commit -m "auto: continuous runner - recursive task assignment ' + new Date().toISOString() + ' [skip ci]"');
  if (!commit.ok) {
    log(`Commit failed: ${commit.err}`);
    return false;
  }
  log(`Committed: ${commit.out}`);
  
  // Push
  const push = exec('git push origin main');
  if (!push.ok) {
    log(`Push failed (maybe need pull first): ${push.err}\nTrying pull --rebase...`);
    const pull = exec('git pull --rebase origin main');
    log(`Pull result: ${pull.out}`);
    const push2 = exec('git push origin main');
    if (!push2.ok) {
      log(`Push still failed: ${push2.err}`);
      return false;
    }
  }
  log('Pushed successfully!');
  return true;
}

function printQueue() {
  const tasks = loadJson(TASKS_PATH);
  const locks = loadJson(LOCKS_PATH);
  const state = loadJson(STATE_PATH);
  
  if (!tasks) {
    log('Failed to load tasks.json');
    return;
  }
  
  log('=== QUEUE STATUS ===');
  tasks.tasks.forEach(t => {
    const deps = (t.dependencies||[]).join(',') || 'none';
    log(`  ${t.priority} ${t.id}: ${t.status} (${t.assignee}) deps:${deps} ${t.status==='blocked' ? 'BLOCKED:'+ (t.blocked||[]).join(';') : ''}`);
  });
  log(`Locks: ${locks ? locks.locks.length : '?'} active`);
  if (locks && locks.locks) {
    locks.locks.forEach(l => log(`  - ${l.agent} -> ${l.taskId} since ${l.since}`));
  }
  if (state && state.version) {
    log(`State v${state.version} lastUpdate ${state.lastUpdate}`);
    if (state.prevTask) log(`  prev: ${state.prevTask.id} ${state.prevTask.status}`);
    if (state.currTask) log(`  curr: ${state.currTask.id} ${state.currTask.status} (${state.currTask.assignee})`);
    if (state.nextTask) log(`  next: ${state.nextTask.id} ${state.nextTask.status} waitingFor:${(state.nextTask.waitingFor||[]).join(',')}`);
  }
  log('====================');
}

async function mainLoop() {
  log('=== CONTINUOUS AUTO-COORDINATOR STARTED ===');
  log(`Repo: ${REPO_PATH}`);
  log(`Check interval: ${CHECK_INTERVAL_MS}ms (60s)`);
  log('Will run forever, checking if agents work and assigning tasks recursively');
  log('Press Ctrl+C to stop (but in background process it never stops)');
  
  let iteration = 0;
  
  while (true) {
    iteration++;
    log(`\n--- ITERATION ${iteration} ---`);
    
    // 1. Fetch latest from origin
    log('Fetching origin...');
    const fetch = exec('git fetch origin main');
    if (fetch.ok) {
      log('Fetch OK');
      // Check if behind
      const behind = exec('git rev-list HEAD..origin/main --count');
      if (behind.ok && parseInt(behind.out.trim()) > 0) {
        log(`Behind origin by ${behind.out.trim()} commits, pulling...`);
        const pull = exec('git pull --rebase origin main');
        log(`Pull: ${pull.out.slice(0,500)}`);
      } else {
        log('Up to date with origin');
      }
    } else {
      log(`Fetch failed: ${fetch.err}`);
    }
    
    // 2. Print current queue
    printQueue();
    
    // 3. Run auto-assign
    runAutoAssign();
    
    // 4. Check and push if changed
    const pushed = checkAndPush();
    
    if (pushed) {
      log('Queue advanced! New tasks assigned and pushed.');
    } else {
      log('No queue advancement this iteration');
    }
    
    // 5. Print next check time
    const next = new Date(Date.now() + CHECK_INTERVAL_MS);
    log(`Next check at ${next.toISOString()} (in 60s)`);
    log(`Iteration ${iteration} complete. Sleeping 60s...`);
    
    // Sleep 60s
    await new Promise(r => setTimeout(r, CHECK_INTERVAL_MS));
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  log('SIGINT received, shutting down...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  log('SIGTERM received, shutting down...');
  process.exit(0);
});

// Start
mainLoop().catch(e => {
  log(`Fatal error in mainLoop: ${e.stack}`);
  process.exit(1);
});
