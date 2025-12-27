#!/usr/bin/env node

/**
 * Hard Reset Script for Docusaurus
 * 
 * Purpose: Clean all build artifacts and caches to fix path corruption
 * issues when switching between WSL and Windows environments.
 * 
 * This script deletes:
 * - .docusaurus/ (build cache)
 * - node_modules/ (dependencies)
 * - build/ (production build)
 * - package-lock.json (lock file)
 * 
 * Then reinstalls dependencies with npm install.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logStep(step, message) {
  log(`\n[${step}] ${message}`, 'cyan');
}

function logSuccess(message) {
  log(`✓ ${message}`, 'green');
}

function logWarning(message) {
  log(`⚠ ${message}`, 'yellow');
}

function logError(message) {
  log(`✗ ${message}`, 'red');
}

/**
 * Recursively delete a directory
 */
function deleteDirectory(dirPath) {
  if (!fs.existsSync(dirPath)) {
    logWarning(`Directory not found: ${dirPath}`);
    return false;
  }

  try {
    fs.rmSync(dirPath, { recursive: true, force: true });
    logSuccess(`Deleted: ${dirPath}`);
    return true;
  } catch (error) {
    logError(`Failed to delete ${dirPath}: ${error.message}`);
    return false;
  }
}

/**
 * Delete a single file
 */
function deleteFile(filePath) {
  if (!fs.existsSync(filePath)) {
    logWarning(`File not found: ${filePath}`);
    return false;
  }

  try {
    fs.unlinkSync(filePath);
    logSuccess(`Deleted: ${filePath}`);
    return true;
  } catch (error) {
    logError(`Failed to delete ${filePath}: ${error.message}`);
    return false;
  }
}

/**
 * Run npm install
 */
function npmInstall() {
  logStep('STEP 5', 'Running npm install...');
  
  try {
    execSync('npm install', { 
      stdio: 'inherit',
      encoding: 'utf-8'
    });
    logSuccess('npm install completed successfully');
    return true;
  } catch (error) {
    logError(`npm install failed: ${error.message}`);
    return false;
  }
}

/**
 * Main execution
 */
function main() {
  log('\n╔════════════════════════════════════════════╗', 'blue');
  log('║   Docusaurus Hard Reset Script            ║', 'blue');
  log('║   Cleaning cache and reinstalling deps    ║', 'blue');
  log('╚════════════════════════════════════════════╝\n', 'blue');

  const projectRoot = path.resolve(__dirname, '..');
  log(`Project root: ${projectRoot}\n`, 'cyan');

  // Step 1: Delete .docusaurus cache
  logStep('STEP 1', 'Deleting .docusaurus cache...');
  deleteDirectory(path.join(projectRoot, '.docusaurus'));

  // Step 2: Delete node_modules
  logStep('STEP 2', 'Deleting node_modules...');
  deleteDirectory(path.join(projectRoot, 'node_modules'));

  // Step 3: Delete build directory
  logStep('STEP 3', 'Deleting build directory...');
  deleteDirectory(path.join(projectRoot, 'build'));

  // Step 4: Delete package-lock.json
  logStep('STEP 4', 'Deleting package-lock.json...');
  deleteFile(path.join(projectRoot, 'package-lock.json'));

  // Step 5: Run npm install
  if (!npmInstall()) {
    logError('\n✗ Hard reset failed during npm install');
    process.exit(1);
  }

  // Success message
  log('\n╔════════════════════════════════════════════╗', 'green');
  log('║   Hard Reset Complete!                     ║', 'green');
  log('║   Your project is ready to build.          ║', 'green');
  log('╚════════════════════════════════════════════╝\n', 'green');

  log('Next steps:', 'cyan');
  log('  • Run: npm start (for development)', 'cyan');
  log('  • Run: npm run build (for production)\n', 'cyan');
}

// Execute main function
try {
  main();
} catch (error) {
  logError(`\nUnexpected error: ${error.message}`);
  process.exit(1);
}
