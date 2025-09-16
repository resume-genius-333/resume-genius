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

  // Define all missing constants with their proper values
  const missingConstants = {
    // Register endpoint
    'registerApiV1AuthRegisterPostBodyLastNameMaxOne': 100,

    // Education creation constants
    'createEducationApiV1ProfileEducationsPostBodyFocusAreaMaxOne': 200,
    'createEducationApiV1ProfileEducationsPostBodyStartDateRegExpOne': '/^\\d{4}-\\d{2}$/',
    'createEducationApiV1ProfileEducationsPostBodyEndDateRegExpOne': '/^\\d{4}-\\d{2}$/',
    'createEducationApiV1ProfileEducationsPostBodyGpaMinOne': 0.0,
    'createEducationApiV1ProfileEducationsPostBodyGpaMaxOne': 5.0,
    'createEducationApiV1ProfileEducationsPostBodyMaxGpaMinOne': 0.0,
    'createEducationApiV1ProfileEducationsPostBodyMaxGpaMaxOne': 5.0,

    // Education update constants
    'updateEducationApiV1ProfileEducationsEducationIdPutBodyInstitutionNameMaxOne': 200,
    'updateEducationApiV1ProfileEducationsEducationIdPutBodyFieldOfStudyMaxOne': 200,
    'updateEducationApiV1ProfileEducationsEducationIdPutBodyFocusAreaMaxOne': 200,
    'updateEducationApiV1ProfileEducationsEducationIdPutBodyStartDateRegExpOne': '/^\\d{4}-\\d{2}$/',
    'updateEducationApiV1ProfileEducationsEducationIdPutBodyEndDateRegExpOne': '/^\\d{4}-\\d{2}$/',
    'updateEducationApiV1ProfileEducationsEducationIdPutBodyGpaMinOne': 0.0,
    'updateEducationApiV1ProfileEducationsEducationIdPutBodyGpaMaxOne': 5.0,
    'updateEducationApiV1ProfileEducationsEducationIdPutBodyMaxGpaMinOne': 0.0,
    'updateEducationApiV1ProfileEducationsEducationIdPutBodyMaxGpaMaxOne': 5.0,

    // Work experience creation constants
    'createWorkExperienceApiV1ProfileWorkExperiencesPostBodyLocationMaxOne': 200,
    'createWorkExperienceApiV1ProfileWorkExperiencesPostBodyStartDateRegExpOne': '/^\\d{4}-\\d{2}$/',
    'createWorkExperienceApiV1ProfileWorkExperiencesPostBodyEndDateRegExpOne': '/^\\d{4}-\\d{2}$/',

    // Work experience update constants
    'updateWorkExperienceApiV1ProfileWorkExperiencesWorkIdPutBodyCompanyNameMaxOne': 200,
    'updateWorkExperienceApiV1ProfileWorkExperiencesWorkIdPutBodyPositionTitleMaxOne': 200,
    'updateWorkExperienceApiV1ProfileWorkExperiencesWorkIdPutBodyLocationMaxOne': 200,
    'updateWorkExperienceApiV1ProfileWorkExperiencesWorkIdPutBodyStartDateRegExpOne': '/^\\d{4}-\\d{2}$/',
    'updateWorkExperienceApiV1ProfileWorkExperiencesWorkIdPutBodyEndDateRegExpOne': '/^\\d{4}-\\d{2}$/',

    // Project creation constants
    'createProjectApiV1ProfileProjectsPostBodyDescriptionMaxOne': 1000,
    'createProjectApiV1ProfileProjectsPostBodyStartDateRegExpOne': '/^\\d{4}-\\d{2}$/',
    'createProjectApiV1ProfileProjectsPostBodyEndDateRegExpOne': '/^\\d{4}-\\d{2}$/',
    'createProjectApiV1ProfileProjectsPostBodyProjectUrlMaxOne': 2083,
    'createProjectApiV1ProfileProjectsPostBodyRepositoryUrlMaxOne': 2083,

    // Project update constants
    'updateProjectApiV1ProfileProjectsProjectIdPutBodyProjectNameMaxOne': 200,
    'updateProjectApiV1ProfileProjectsProjectIdPutBodyDescriptionMaxOne': 1000,
    'updateProjectApiV1ProfileProjectsProjectIdPutBodyStartDateRegExpOne': '/^\\d{4}-\\d{2}$/',
    'updateProjectApiV1ProfileProjectsProjectIdPutBodyEndDateRegExpOne': '/^\\d{4}-\\d{2}$/',
    'updateProjectApiV1ProfileProjectsProjectIdPutBodyProjectUrlMaxOne': 2083,
    'updateProjectApiV1ProfileProjectsProjectIdPutBodyRepositoryUrlMaxOne': 2083,
  };

  // Find all references to constants in the file
  const constantRefs = content.match(/[a-zA-Z]+ApiV1[a-zA-Z]+(?:Min|Max|Default|RegExp)[a-zA-Z0-9]*/g) || [];

  // Find all defined constants
  const definedConstants = content.match(/export const [a-zA-Z]+ApiV1[a-zA-Z]+[a-zA-Z0-9]* =/g) || [];
  const defined = definedConstants.map(c => c.replace('export const ', '').replace(' =', ''));

  // Find undefined constants
  const undefinedConsts = [...new Set(constantRefs)].filter(ref => !defined.includes(ref));

  // Add missing constant definitions
  let insertions = [];
  let addedCount = 0;

  for (const constName of undefinedConsts) {
    if (missingConstants[constName] !== undefined) {
      const value = missingConstants[constName];
      // Format the value properly (RegExp patterns need special handling)
      const formattedValue = typeof value === 'string' && value.startsWith('/')
        ? value  // RegExp pattern
        : JSON.stringify(value);

      insertions.push(`export const ${constName} = ${formattedValue};`);
      addedCount++;
    } else {
      console.warn(`⚠️  Unknown constant: ${constName} - needs manual configuration`);
    }
  }

  if (insertions.length > 0) {
    // Find a good place to insert - after the imports but before the first schema
    const firstSchemaIndex = content.indexOf('export const');

    if (firstSchemaIndex !== -1) {
      // Insert all constants at once, right before the first export
      const insertionText = insertions.join('\n') + '\n\n';
      content = content.slice(0, firstSchemaIndex) + insertionText + content.slice(firstSchemaIndex);

      console.log(`✅ Added ${addedCount} missing constants`);
      insertions.slice(0, 5).forEach(c => console.log(`   - ${c.split(' ')[2]}`));
      if (insertions.length > 5) {
        console.log(`   ... and ${insertions.length - 5} more`);
      }
    }
  } else if (undefinedConsts.length === 0) {
    console.log('✅ No missing constants found');
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