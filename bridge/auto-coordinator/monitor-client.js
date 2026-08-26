#!/usr/bin/env node
// Monitor Client Agent - Checks if client is working or has problem
// Reports to lead engineer / auto-coordinator
// Runs every 60s alongside continuous runner

const fs = require('fs');
const path = require('path');

const REPO_PATH = path.join(__dirname, '../..');
const TASKS_PATH = path.join(REPO_PATH, 'bridge/tasks.json');
const LOCKS_PATH = path.join(REPO_PATH, 'bridge/locks.json');
const STATE_PATH = path.join(REPO_PATH, 'bridge/state.json');
const QUESTIONS_PATH = path.join(REPO_PATH, 'bridge/questions.md');

function log(msg) {
  console.log(`[CLIENT-MONITOR ${new Date().toISOString()}] ${msg}`);
}

function loadJson(p) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (e) {
    return null;
  }
}

function checkClient() {
  const tasks = loadJson(TASKS_PATH);
  const locks = loadJson(LOCKS_PATH);
  const state = loadJson(STATE_PATH);
  
  if (!tasks) {
    log('ERROR: Cannot load tasks.json');
    return { status: 'error', problem: 'tasks.json not found' };
  }
  
  const clientTasks = tasks.tasks.filter(t => t.assignee === 'client-agent');
  const done = clientTasks.filter(t => t.status === 'done');
  const inProgress = clientTasks.filter(t => t.status === 'in_progress');
  const todo = clientTasks.filter(t => t.status === 'todo');
  const blocked = clientTasks.filter(t => t.status === 'blocked');
  
  log(`Client Agent Tasks: ${clientTasks.length} total - ${done.length} DONE, ${inProgress.length} IN_PROGRESS, ${todo.length} TODO, ${blocked.length} BLOCKED`);
  
  clientTasks.forEach(t => {
    log(`  - ${t.id}: ${t.status} ${t.blocked && t.blocked.length ? 'BLOCKED:'+t.blocked.join(';') : ''}`);
  });
  
  // Check locks
  const clientLocks = locks ? locks.locks.filter(l => l.agent === 'client-agent') : [];
  log(`Client locks: ${clientLocks.length}`);
  clientLocks.forEach(l => log(`  - ${l.taskId} files: ${l.files.join(', ')}`));
  
  // Detect problems
  const problems = [];
  
  if (blocked.length > 0) {
    blocked.forEach(t => {
      problems.push(`BLOCKED: ${t.id} - ${t.blocked.join(', ')}`);
    });
  }
  
  if (inProgress.length > 0) {
    inProgress.forEach(t => {
      const claimedAt = t.claimedAt ? new Date(t.claimedAt) : null;
      const now = new Date();
      const hours = claimedAt ? (now - claimedAt) / 1000 / 3600 : 0;
      if (hours > 24) {
        problems.push(`STUCK: ${t.id} IN_PROGRESS for ${hours.toFixed(1)}h since ${t.claimedAt} - no push`);
      }
    });
  }
  
  if (done.length === clientTasks.length && clientTasks.length > 0) {
    log('Client has completed all assigned tasks - waiting for new task');
    // Check if there are unassigned tasks that client could take
    const unassigned = tasks.tasks.filter(t => t.status === 'todo' && (t.role === 'client' || t.role === 'peinture'));
    if (unassigned.length > 0) {
      log(`Found ${unassigned.length} TODO tasks that client could take: ${unassigned.map(t=>t.id).join(', ')}`);
      problems.push(`WAITING: Client DONE all tasks, has no next task. Available TODO: ${unassigned.map(t=>t.id).join(', ')} - needs dispatch`);
    } else {
      log('No TODO tasks available for client - queue waiting for dependencies');
    }
  }
  
  if (todo.length > 0) {
    log(`Client has ${todo.length} TODO tasks not started`);
    todo.forEach(t => {
      const deps = t.dependencies || [];
      const depsMet = deps.every(depId => {
        const dep = tasks.tasks.find(x => x.id === depId);
        return dep && dep.status === 'done';
      });
      if (!depsMet) {
        problems.push(`WAITING_DEPS: ${t.id} TODO but deps not met: ${deps.filter(d => { const dep=tasks.tasks.find(x=>x.id===d); return !dep || dep.status!=='done'; }).join(', ')}`);
      }
    });
  }
  
  if (problems.length === 0) {
    log('Client Agent OK - no problems detected');
    return { status: 'ok', clientTasks, problems: [] };
  } else {
    log(`PROBLEMS DETECTED for client-agent:`);
    problems.forEach(p => log(`  ! ${p}`));
    
    // Write to questions.md
    try {
      let qContent = fs.readFileSync(QUESTIONS_PATH, 'utf8');
      const newQ = `\n### Q-CLIENT-${Date.now()}: Client Agent Status Check\n**From:** client-monitor\n**To:** lead-engineer / auto-coordinator\n**Date:** ${new Date().toISOString()}\n**Status:** ${inProgress.length ? 'IN_PROGRESS' : done.length===clientTasks.length ? 'WAITING' : 'TODO'}\n**Problems:**\n${problems.map(p=>`- ${p}`).join('\n')}\n**Client Tasks:** ${clientTasks.map(t=>`${t.id}=${t.status}`).join(', ')}\n**Locks:** ${clientLocks.length}\n**Action Needed:** ${blocked.length ? 'Unblock SQL/RLS' : done.length===clientTasks.length ? 'Dispatch next task to client' : 'Nudge client-agent'}\n`;
      
      // Append if not already exists recently
      if (!qContent.includes('Q-CLIENT-') || !qContent.includes(problems[0].slice(0,30))) {
        fs.appendFileSync(QUESTIONS_PATH, newQ);
        log('Wrote problem to bridge/questions.md');
      }
    } catch (e) {
      log(`Failed to write questions.md: ${e.message}`);
    }
    
    return { status: 'problem', clientTasks, problems, locks: clientLocks };
  }
}

// Run once
const result = checkClient();
console.log(JSON.stringify(result, null, 2));
