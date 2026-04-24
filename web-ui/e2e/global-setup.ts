import { execSync } from 'child_process';
import path from 'path';

async function globalSetup() {
  console.log('Running global setup: Seeding E2E data...');
  const scriptPath = path.resolve(import.meta.dirname, '../../tests/seed_e2e.py');
  try {
    execSync(`python "${scriptPath}"`, { stdio: 'inherit' });
    // Also try uv run python just in case
  } catch (error) {
    try {
      execSync(`uv run python "${scriptPath}"`, { stdio: 'inherit', cwd: path.resolve(import.meta.dirname, '../../') });
    } catch (e) {
      console.error('Failed to seed E2E data', e);
      throw e;
    }
  }
}

export default globalSetup;
