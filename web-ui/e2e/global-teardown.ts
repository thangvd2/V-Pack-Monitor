import { execSync } from 'child_process';
import path from 'path';

async function globalTeardown() {
  console.log('Running global teardown: Cleaning up E2E data...');
  const scriptPath = path.resolve(import.meta.dirname, '../../tests/seed_e2e.py');
  try {
    execSync(`python "${scriptPath}" cleanup`, { stdio: 'inherit' });
  } catch (error) {
    try {
      execSync(`uv run python "${scriptPath}" cleanup`, {
        stdio: 'inherit',
        cwd: path.resolve(import.meta.dirname, '../../'),
      });
    } catch (e) {
      console.error('Failed to cleanup E2E data', e);
    }
  }
}

export default globalTeardown;
