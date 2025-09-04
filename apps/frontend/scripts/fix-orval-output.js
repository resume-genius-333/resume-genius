#!/usr/bin/env node

/**
 * Post-processing script to fix issues in Orval-generated code
 * This script:
 * 1. Adds missing constant definitions
 * 2. Fixes any import issues
 * 3. Formats all generated files with Prettier
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);
const GENERATED_DIR = path.join(__dirname, '..', 'src', 'lib', 'api', 'generated');

function fixZodFile() {
  const zodFilePath = path.join(GENERATED_DIR, 'api.zod.ts');
  
  if (!fs.existsSync(zodFilePath)) {
    console.log('Zod file not found, skipping...');
    return;
  }
  
  let content = fs.readFileSync(zodFilePath, 'utf8');
  
  // Add missing constant definitions after the existing ones
  // Check if the constant is missing and add it
  if (content.includes('registerApiV1AuthRegisterPostBodyLastNameMaxOne') && 
      !content.includes('export const registerApiV1AuthRegisterPostBodyLastNameMaxOne')) {
    
    // Find where to insert the constant (after the FirstNameMax constant)
    const insertAfter = 'export const registerApiV1AuthRegisterPostBodyFirstNameMax = 100;';
    const insertIndex = content.indexOf(insertAfter);
    
    if (insertIndex !== -1) {
      const endOfLine = content.indexOf('\n', insertIndex);
      const insertion = '\nexport const registerApiV1AuthRegisterPostBodyLastNameMaxOne = 100;';
      content = content.slice(0, endOfLine) + insertion + content.slice(endOfLine);
      console.log('✅ Added missing constant: registerApiV1AuthRegisterPostBodyLastNameMaxOne');
    }
  }
  
  fs.writeFileSync(zodFilePath, content);
}

function fixApiFile() {
  const apiFilePath = path.join(GENERATED_DIR, 'api.ts');
  
  if (!fs.existsSync(apiFilePath)) {
    console.log('API file not found, skipping...');
    return;
  }
  
  let content = fs.readFileSync(apiFilePath, 'utf8');
  
  // The axios-functions client should use the custom axios instance correctly
  // No fixes needed for now, but keeping this function for future use
  
  fs.writeFileSync(apiFilePath, content);
}

async function prettifyGeneratedFiles() {
  console.log('🎨 Formatting generated files with Prettier...');
  
  try {
    // Check if prettier is installed
    await execAsync('npx prettier --version');
    
    // Format all TypeScript files in the generated directory
    const { stdout, stderr } = await execAsync(
      `npx prettier --write "${GENERATED_DIR}/**/*.{ts,tsx}"`,
      { cwd: path.join(__dirname, '..') }
    );
    
    if (stderr) {
      console.warn('⚠️  Prettier warnings:', stderr);
    }
    
    // Count formatted files
    const files = fs.readdirSync(GENERATED_DIR);
    const tsFiles = files.filter(f => f.endsWith('.ts'));
    
    // Also format files in schemas directory
    const schemasDir = path.join(GENERATED_DIR, 'schemas');
    if (fs.existsSync(schemasDir)) {
      const schemaFiles = fs.readdirSync(schemasDir);
      const schemaTsFiles = schemaFiles.filter(f => f.endsWith('.ts'));
      console.log(`✅ Formatted ${tsFiles.length + schemaTsFiles.length} TypeScript files`);
    } else {
      console.log(`✅ Formatted ${tsFiles.length} TypeScript files`);
    }
    
  } catch (error) {
    console.error('❌ Prettier formatting failed:', error.message);
    console.log('💡 Make sure Prettier is installed: pnpm add -D prettier');
  }
}

// Main execution
async function main() {
  console.log('🔧 Fixing Orval-generated files...');
  
  // Run fixes
  fixZodFile();
  fixApiFile();
  
  // Format with Prettier
  await prettifyGeneratedFiles();
  
  console.log('✨ Done!');
}

// Run the script
main().catch(error => {
  console.error('❌ Script failed:', error);
  process.exit(1);
});