#!/usr/bin/env node
// Monitor Admin Agent - Checks if admin is working or has problem
// Reports to lead engineer / auto-coordinator

const fs = require('fs');
const path = require('path');

const REPO_PATH = path.join(__dirname, '../..');
const TASKS_PATH = path.join(REPO_PATH, 'bridge/tasks.json');
const LOCKS_PATH = path.join(REPO_PATH, 'bridge/locks.json');
const STATE_PATH = path.join(REPO_PATH, 'bridge/state.json');
const QUESTIONS_PATH = path.join(REPO_PATH, 'bridge/questions.md');

function log(msg) {
  console.log(`[ADMIN-MONITOR ${new Date().toISOString()}] ${msg}`);
}

function loadJson(p) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (e) {
    return null;
  }
}

function checkAdmin() {
  const tasks = loadJson(TASKS_PATH);
  const locks = loadJson(LOCKS_PATH);
  
  if (!tasks) {
    log('ERROR: Cannot load tasks.json');
    return { status: 'error' };
  }
  
  const adminTasks = tasks.tasks.filter(t => t.assignee === 'admin-agent');
  const done = adminTasks.filter(t => t.status === 'done');
  const inProgress = adminTasks.filter(t => t.status === 'in_progress');
  const todo = adminTasks.filter(t => t.status === 'todo');
  const blocked = adminTasks.filter(t => t.status === 'blocked');
  
  log(`Admin Agent Tasks: ${adminTasks.length} total - ${done.length} DONE, ${inProgress.length} IN_PROGRESS, ${todo.length} TODO, ${blocked.length} BLOCKED`);
  
  adminTasks.forEach(t => {
    log(`  - ${t.id}: ${t.status} ${t.blocked && t.blocked.length ? 'BLOCKED:'+t.blocked.join(';') : ''} claimedAt=${t.claimedAt||'none'}`);
  });
  
  const adminLocks = locks ? locks.locks.filter(l => l.agent === 'admin-agent') : [];
  log(`Admin locks: ${adminLocks.length}`);
  adminLocks.forEach(l => log(`  - ${l.taskId} files: ${l.files.join(', ')}`));
  
  const problems = [];
  
  if (blocked.length > 0) {
    blocked.forEach(t => problems.push(`BLOCKED: ${t.id} - ${t.blocked.join(', ')}`));
  }
  
  if (inProgress.length > 0) {
    inProgress.forEach(t => {
      const claimedAt = t.claimedAt ? new Date(t.claimedAt) : null;
      const now = new Date();
      const hours = claimedAt ? (now - claimedAt) / 1000 / 3600 : 0;
      if (hours > 24) {
        problems.push(`STUCK: ${t.id} IN_PROGRESS for ${hours.toFixed(1)}h since ${t.claimedAt}`);
      } else {
        log(`Admin task ${t.id} IN_PROGRESS for ${hours.toFixed(1)}h - OK (recent)`);
      }
    });
  }
  
  if (adminTasks.length === 0) {
    problems.push('NO_TASK: No tasks assigned to admin-agent');
  }
  
  if (todo.length > 0) {
    todo.forEach(t => {
      const deps = t.dependencies || [];
      const depsMet = deps.every(depId => {
        const dep = tasks.tasks.find(x => x.id === depId);
        return dep && dep.status === 'done';
      });
      if (!depsMet) {
        const waiting = deps.filter(d => { const dep=tasks.tasks.find(x=>x.id===d); return !dep || dep.status!=='done'; });
        problems.push(`WAITING_DEPS: ${t.id} TODO but waiting ${waiting.join(', ')}`);
      }
    });
  }
  
  if (problems.length === 0) {
    log('Admin Agent OK - working or ready');
    return { status: 'ok', adminTasks, problems: [] };
  } else {
    log('PROBLEMS for admin-agent:');
    problems.forEach(p => log(`  ! ${p}`));
    return { status: 'problem', adminTasks, problems, locks: adminLocks };
  }
}

const result = checkAdmin();
console.log(JSON.stringify(result, null, 2));
