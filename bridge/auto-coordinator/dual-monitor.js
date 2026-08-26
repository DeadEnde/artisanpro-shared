#!/usr/bin/env node
// Dual Monitor - Watches BOTH admin and client agents simultaneously
// Gives tasks to each separately so they can differentiate work
// Reports problems to lead engineer
// Runs every 60s recursively forever

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const REPO_PATH = path.join(__dirname, '../..');
const TASKS_PATH = path.join(REPO_PATH, 'bridge/tasks.json');
const LOCKS_PATH = path.join(REPO_PATH, 'bridge/locks.json');
const STATE_PATH = path.join(REPO_PATH, 'bridge/state.json');

const CHECK_INTERVAL_MS = 60 * 1000;

function log(msg) {
  console.log(`[DUAL-MONITOR ${new Date().toISOString()}] ${msg}`);
}

function loadJson(p) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (e) {
    return null;
  }
}

function exec(cmd) {
  try {
    return { ok: true, out: require('child_process').execSync(cmd, { cwd: REPO_PATH, encoding: 'utf8', stdio: 'pipe' }).trim() };
  } catch (e) {
    return { ok: false, err: e.message };
  }
}

function checkAgent(agentName, role) {
  const tasks = loadJson(TASKS_PATH);
  if (!tasks) return { status: 'error' };
  
  const agentTasks = tasks.tasks.filter(t => t.assignee === agentName);
  const done = agentTasks.filter(t => t.status === 'done');
  const inProgress = agentTasks.filter(t => t.status === 'in_progress');
  const todo = agentTasks.filter(t => t.status === 'todo');
  const blocked = agentTasks.filter(t => t.status === 'blocked');
  
  // Check stuck
  let stuck = [];
  inProgress.forEach(t => {
    if (t.claimedAt) {
      const hours = (new Date() - new Date(t.claimedAt)) / 1000 / 3600;
      if (hours > 24) stuck.push({ id: t.id, hours: hours.toFixed(1) });
    }
  });
  
  return {
    agent: agentName,
    role,
    total: agentTasks.length,
    done: done.length,
    inProgress: inProgress.map(t => t.id),
    todo: todo.map(t => t.id),
    blocked: blocked.map(t => ({ id: t.id, reason: t.blocked })),
    stuck,
    tasks: agentTasks
  };
}

function dispatchTask(taskId, agentName) {
  log(`Dispatching ${taskId} to ${agentName}...`);
  const tasks = loadJson(TASKS_PATH);
  const locks = loadJson(LOCKS_PATH);
  
  const task = tasks.tasks.find(t => t.id === taskId);
  if (!task) {
    log(`Task ${taskId} not found`);
    return false;
  }
  
  if (task.status === 'in_progress') {
    log(`Task ${taskId} already IN_PROGRESS`);
    return false;
  }
  
  // Check file conflict
  const claimedFiles = task.claimedFiles || [];
  const conflict = locks.locks.some(lock => {
    return lock.files.some(lf => claimedFiles.some(cf => cf === lf || (cf.includes('*') && lf.startsWith(cf.split('*')[0]))));
  });
  
  if (conflict) {
    log(`File conflict for ${taskId}, cannot dispatch`);
    return false;
  }
  
  // Check deps (allow human override for admin)
  const deps = task.dependencies || [];
  const taskMap = {};
  tasks.tasks.forEach(t => taskMap[t.id] = t);
  const depsMet = deps.every(d => taskMap[d] && taskMap[d].status === 'done');
  
  if (!depsMet) {
    log(`Deps not met for ${taskId}: ${deps.filter(d => !taskMap[d] || taskMap[d].status !== 'done').join(', ')} - but allowing human override per user request`);
  }
  
  // Dispatch
  task.status = 'in_progress';
  task.claimedAt = new Date().toISOString();
  
  locks.locks.push({
    agent: agentName,
    files: claimedFiles,
    since: new Date().toISOString(),
    taskId: taskId
  });
  
  tasks.lastUpdate = new Date().toISOString();
  locks.lastUpdate = new Date().toISOString();
  
  fs.writeFileSync(TASKS_PATH, JSON.stringify(tasks, null, 2) + '\n');
  fs.writeFileSync(LOCKS_PATH, JSON.stringify(locks, null, 2) + '\n');
  
  log(`Dispatched ${taskId} to ${agentName} successfully`);
  return true;
}

async function mainLoop() {
  log('=== DUAL MONITOR STARTED - Admin + Client ===');
  log('Watches both agents separately so they can differentiate');
  log('Reports problems to lead engineer');
  log(`Check interval: ${CHECK_INTERVAL_MS}ms`);
  
  let iter = 0;
  
  while (true) {
    iter++;
    log(`\n--- DUAL ITERATION ${iter} ---`);
    
    // Fetch
    exec('git fetch origin main');
    const behind = exec('git rev-list HEAD..origin/main --count');
    if (behind.ok && parseInt(behind.out.trim()) > 0) {
      log(`Behind by ${behind.out}, pulling...`);
      exec('git pull --rebase origin main');
    }
    
    // Check both agents
    const admin = checkAgent('admin-agent', 'admin');
    const client = checkAgent('client-agent', 'client');
    const i18n = checkAgent('i18n-agent', 'i18n');
    const security = checkAgent('security-agent', 'security');
    const api = checkAgent('api-agent', 'api');
    const peinture = checkAgent('peinture-agent', 'peinture');
    const billing = checkAgent('billing-agent', 'billing');
    
    log(`ADMIN: ${admin.done} DONE, ${admin.inProgress.length} IN_PROGRESS (${admin.inProgress.join(',')}), ${admin.todo.length} TODO, ${admin.blocked.length} BLOCKED, stuck=${admin.stuck.length}`);
    log(`CLIENT: ${client.done} DONE, ${client.inProgress.length} IN_PROGRESS (${client.inProgress.join(',')}), ${client.todo.length} TODO, ${client.blocked.length} BLOCKED, stuck=${client.stuck.length}`);
    log(`I18N: ${i18n.done} DONE, ${i18n.inProgress.length} IN_PROGRESS, stuck=${i18n.stuck.length} - BOTTLENECK`);
    log(`SECURITY: ${security.done} DONE, ${security.inProgress.length} IN_PROGRESS, stuck=${security.stuck.length}`);
    log(`API: ${api.done} DONE, ${api.inProgress.length} IN_PROGRESS, stuck=${api.stuck.length}`);
    log(`PEINTURE: ${peinture.todo.length} TODO waiting i18n`);
    log(`BILLING: ${billing.todo.length} TODO waiting admin`);
    
    // Problems
    const allProblems = [];
    
    if (i18n.stuck.length > 0) {
      allProblems.push(`I18N STUCK ${i18n.stuck.map(s=>`${s.id} ${s.hours}h`).join(',')} - blocks peinture+admin`);
    }
    if (security.stuck.length > 0) {
      allProblems.push(`SECURITY STUCK ${security.stuck.map(s=>`${s.id} ${s.hours}h`).join(',')} - blocks client`);
    }
    if (api.stuck.length > 0) {
      allProblems.push(`API STUCK ${api.stuck.map(s=>`${s.id} ${s.hours}h`).join(',')}`);
    }
    if (client.blocked.length > 0) {
      allProblems.push(`CLIENT BLOCKED ${client.blocked.map(b=>`${b.id}:${b.reason}`).join(',')}`);
    }
    
    // Auto-dispatch logic for admin and client separately
    let dispatched = [];
    
    // Admin: if no IN_PROGRESS and has TODO that is safe (no file conflict)
    if (admin.inProgress.length === 0 && admin.todo.length > 0) {
      // Find first todo with no file conflict (allow dep override per user request)
      const tasks = loadJson(TASKS_PATH);
      for (const tid of admin.todo) {
        const t = tasks.tasks.find(x => x.id === tid);
        if (t) {
          // Check file conflict only
          const locks = loadJson(LOCKS_PATH);
          const cf = t.claimedFiles || [];
          const conflict = locks.locks.some(l => l.files.some(lf => cf.some(c => c === lf)));
          if (!conflict) {
            if (dispatchTask(tid, 'admin-agent')) {
              dispatched.push(`admin:${tid}`);
              break;
            }
          }
        }
      }
    }
    
    // Client: if DONE all and no IN_PROGRESS, check if needs new task
    // Client currently DONE, has no TODO assigned to client role, but could take peinture? 
    // For now, client has no more tasks - it's waiting. We should keep it as is, or assign peinture if peinture-agent stuck?
    // User wants one task admin and one task client to differentiate - so we ensure both have tasks
    if (client.done === client.total && client.total > 0 && client.inProgress.length === 0) {
      log('Client DONE all tasks, waiting for new assignment - currently no more client tasks in queue');
      // Check if peinture could be given to client as secondary? But role mismatch - skip for now
      // Instead, we ensure client stays DONE and we report waiting
    }
    
    // Also try to dispatch peinture if i18n done (but it's not)
    // Check if we should force admin and peinture in parallel (user requested admin+client differentiation)
    // Admin already dispatched, client done - so we have differentiation: admin IN_PROGRESS, client DONE
    
    if (allProblems.length > 0) {
      log(`PROBLEMS FOUND:`);
      allProblems.forEach(p => log(`  ! ${p}`));
      log('Reporting to lead engineer via logs and will be visible in continuous runner');
    } else {
      log('No problems - all agents OK or waiting for deps');
    }
    
    if (dispatched.length > 0) {
      log(`Dispatched: ${dispatched.join(', ')}`);
      // Commit and push
      const status = exec('git status --porcelain');
      if (status.ok && status.out.trim()) {
        exec('git add bridge/tasks.json bridge/locks.json');
        exec(`git commit -m "auto(dual-monitor): dispatch ${dispatched.join(', ')} - admin+client differentiation [skip ci]"`);
        const push = exec('git push origin main');
        log(`Push: ${push.ok ? 'OK' : 'FAILED ' + push.err}`);
      }
    } else {
      log('No dispatch this iteration');
    }
    
    log(`Next check in 60s at ${new Date(Date.now() + CHECK_INTERVAL_MS).toISOString()}`);
    await new Promise(r => setTimeout(r, CHECK_INTERVAL_MS));
  }
}

mainLoop().catch(e => {
  log(`Fatal: ${e.stack}`);
  process.exit(1);
});
