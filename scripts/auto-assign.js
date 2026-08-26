#!/usr/bin/env node
// Auto-Coordinator - Automatically assigns next tasks when agents push
// Runs in GitHub Action or locally
// Lead Engineer: 2026-08-25

const fs = require('fs');
const path = require('path');

const TASKS_PATH = path.join(__dirname, '../bridge/tasks.json');
const LOCKS_PATH = path.join(__dirname, '../bridge/locks.json');
const STATE_PATH = path.join(__dirname, '../bridge/state.json');
const AGENTS_PATH = path.join(__dirname, '../bridge/agents.md');

function loadJson(p) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (e) {
    console.error(`Failed to load ${p}:`, e.message);
    return null;
  }
}

function saveJson(p, data) {
  fs.writeFileSync(p, JSON.stringify(data, null, 2) + '\n', 'utf8');
}

function log(msg) {
  console.log(`[AUTO-COORDINATOR ${new Date().toISOString()}] ${msg}`);
}

function main() {
  log('Starting auto-assign check...');

  const tasksData = loadJson(TASKS_PATH);
  const locksData = loadJson(LOCKS_PATH);
  const stateData = loadJson(STATE_PATH);

  if (!tasksData || !locksData || !stateData) {
    log('Missing bridge files, aborting');
    process.exit(1);
  }

  let changed = false;
  const newlyAssigned = [];

  // 1. Check for completed tasks - release their locks if still present but task is done
  const doneTaskIds = tasksData.tasks.filter(t => t.status === 'done').map(t => t.id);
  const activeLocks = locksData.locks || [];
  const locksToKeep = [];

  for (const lock of activeLocks) {
    if (doneTaskIds.includes(lock.taskId)) {
      log(`Releasing lock for done task ${lock.taskId} (agent ${lock.agent})`);
      changed = true;
      // Don't keep this lock
    } else {
      locksToKeep.push(lock);
    }
  }

  if (locksToKeep.length !== activeLocks.length) {
    locksData.locks = locksToKeep;
    locksData.lastUpdate = new Date().toISOString();
    saveJson(LOCKS_PATH, locksData);
    changed = true;
  }

  // 2. Auto-assign next tasks where dependencies are met
  const taskMap = {};
  tasksData.tasks.forEach(t => taskMap[t.id] = t);

  for (const task of tasksData.tasks) {
    if (task.status !== 'todo') continue;

    // Check dependencies
    const deps = task.dependencies || [];
    const depsMet = deps.every(depId => {
      const dep = taskMap[depId];
      return dep && dep.status === 'done';
    });

    if (!depsMet) {
      log(`Task ${task.id} waiting for dependencies: ${deps.filter(d => taskMap[d]?.status !== 'done').join(', ')}`);
      continue;
    }

    // Check file lock conflicts
    const claimedFiles = task.claimedFiles || [];
    const conflict = locksData.locks.some(lock => {
      return lock.files.some(lockedFile => {
        return claimedFiles.some(cf => {
          // Simple glob check: if cf contains * or lockedFile contains *
          if (cf.includes('*') || lockedFile.includes('*')) {
            const base1 = cf.split('*')[0];
            const base2 = lockedFile.split('*')[0];
            return base1 && base2 && (lockedFile.startsWith(base1) || cf.startsWith(base2));
          }
          return cf === lockedFile;
        });
      });
    });

    if (conflict) {
      log(`Task ${task.id} has file lock conflict, skipping`);
      continue;
    }

    // Auto-assign!
    log(`Auto-assigning task ${task.id} to ${task.assignee} (role: ${task.role})`);
    task.status = 'in_progress';
    task.claimedAt = new Date().toISOString();
    newlyAssigned.push(task);

    // Add lock
    locksData.locks.push({
      agent: task.assignee,
      files: claimedFiles,
      since: new Date().toISOString(),
      taskId: task.id
    });

    changed = true;
  }

  if (newlyAssigned.length > 0) {
    tasksData.lastUpdate = new Date().toISOString();
    saveJson(TASKS_PATH, tasksData);
    locksData.lastUpdate = new Date().toISOString();
    saveJson(LOCKS_PATH, locksData);

    // Update state.json
    stateData.lastUpdate = new Date().toISOString();
    stateData.currentTasks = {};
    tasksData.tasks.forEach(t => {
      stateData.currentTasks[t.id] = t.status;
    });
    stateData.lastCoordinatorMessage = `Auto-assigned ${newlyAssigned.length} tasks: ${newlyAssigned.map(t => t.id).join(', ')} at ${new Date().toISOString()}`;
    if (stateData.inProgress) {
      stateData.inProgress = stateData.inProgress.filter(i => !i.includes('Auto-assigned'));
      stateData.inProgress.push(`Auto-assigned ${newlyAssigned.length} tasks: ${newlyAssigned.map(t => t.id).join(', ')}`);
    }
    saveJson(STATE_PATH, stateData);

    log(`Successfully auto-assigned ${newlyAssigned.length} tasks`);
    
    // Output for GitHub Action
    if (process.env.GITHUB_OUTPUT) {
      fs.appendFileSync(process.env.GITHUB_OUTPUT, `assigned=${newlyAssigned.map(t => t.id).join(',')}\n`);
      fs.appendFileSync(process.env.GITHUB_OUTPUT, `count=${newlyAssigned.length}\n`);
    }
  } else {
    log('No new tasks to auto-assign');
  }

  // 3. Summary
  log('=== CURRENT STATUS ===');
  tasksData.tasks.forEach(t => {
    log(`${t.priority} ${t.id}: ${t.status} (${t.assignee}) deps: ${(t.dependencies||[]).join(',')||'none'}`);
  });
  log(`Locks: ${locksData.locks.length} active`);
  locksData.locks.forEach(l => log(`  - ${l.agent} -> ${l.taskId}: ${l.files.join(', ')}`));

  if (changed) {
    log('Changes made - should commit & push');
    // For GitHub Action, set output
    if (process.env.GITHUB_OUTPUT) {
      fs.appendFileSync(process.env.GITHUB_OUTPUT, `changed=true\n`);
    }
    process.exit(0); // Signal that changes were made
  } else {
    log('No changes needed');
    if (process.env.GITHUB_OUTPUT) {
      fs.appendFileSync(process.env.GITHUB_OUTPUT, `changed=false\n`);
    }
  }
}

main();
