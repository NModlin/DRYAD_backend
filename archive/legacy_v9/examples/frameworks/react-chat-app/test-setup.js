/**
 * Dryad Console Setup Test
 *
 * This script tests the basic setup and configuration of the Dryad Console.
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 Testing Dryad Console Setup...\n');

// Check if all required files exist
const requiredFiles = [
  'package.json',
  'src/App.tsx',
  'src/dryad-client.ts',
  '.env.example',
  'setup.bat',
  'setup.sh',
  'README.md'
];

console.log('📁 Checking required files:');
let allFilesExist = true;

requiredFiles.forEach(file => {
  const filePath = path.join(__dirname, file);
  if (fs.existsSync(filePath)) {
    console.log(`✅ ${file}`);
  } else {
    console.log(`❌ ${file} - MISSING`);
    allFilesExist = false;
  }
});

console.log('\n📦 Checking package.json dependencies:');
try {
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  const requiredDeps = ['react', 'axios', 'styled-components', 'react-markdown', 'react-syntax-highlighter'];
  
  requiredDeps.forEach(dep => {
    if (packageJson.dependencies && packageJson.dependencies[dep]) {
      console.log(`✅ ${dep} - ${packageJson.dependencies[dep]}`);
    } else {
      console.log(`❌ ${dep} - NOT FOUND in dependencies`);
      allFilesExist = false;
    }
  });
} catch (error) {
  console.log('❌ Failed to read package.json');
  allFilesExist = false;
}

console.log('\n🔧 Checking API client structure:');
try {
  const dryadClient = fs.readFileSync('src/dryad-client.ts', 'utf8');
  const requiredMethods = ['getSystemHealth', 'createConversation', 'invokeAgent', 'getAgents'];
  
  requiredMethods.forEach(method => {
    if (dryadClient.includes(method)) {
      console.log(`✅ ${method} method found`);
    } else {
      console.log(`❌ ${method} method NOT FOUND`);
      allFilesExist = false;
    }
  });
} catch (error) {
  console.log('❌ Failed to read dryad-client.ts');
  allFilesExist = false;
}

console.log('\n🎯 Setup Test Results:');
if (allFilesExist) {
  console.log('✅ ALL CHECKS PASSED - Setup is ready!');
  console.log('\nNext steps:');
  console.log('1. Run setup.bat (Windows) or setup.sh (Linux/Mac)');
  console.log('2. Configure .env file with your Dryad backend URL');
  console.log('3. Run "npm start" to launch the chat interface');
  console.log('4. Ensure Dryad backend is running on http://localhost:8000');
} else {
  console.log('❌ SOME CHECKS FAILED - Please review the missing components');
  console.log('\nTroubleshooting:');
  console.log('- Check that all files were created successfully');
  console.log('- Verify package.json has the correct dependencies');
  console.log('- Ensure the dryad-client.ts file contains all required methods');
}

console.log('\n🚀 Ready to connect to Dryad.AI backend!');