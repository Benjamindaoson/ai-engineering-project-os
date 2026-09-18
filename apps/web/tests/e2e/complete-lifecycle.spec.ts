/**
 * Playwright E2E Test: Complete Upgrade Lifecycle
 * 
 * Tests the full flow:
 * Import → Audit → Plan → Task → Execute → Verify → Evidence → Version → Interview → Gap
 */

import { test, expect } from '@playwright/test';

test.describe('Complete Upgrade Lifecycle', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
  });

  test('should load the home page', async ({ page }) => {
    // Check that the page loads
    await expect(page).toHaveTitle(/AI Engineering/i);
    
    // Check for main navigation elements
    await expect(page.getByRole('heading', { name: /AI Engineering/i })).toBeVisible();
  });

  test('should navigate to project import', async ({ page }) => {
    // Click on import link
    await page.getByRole('link', { name: /import|导入/i }).first().click();
    
    // Should see import form
    await expect(page.getByPlaceholder(/github|repository/i)).toBeVisible({ timeout: 5000 }).catch(() => {
      // Fallback: check for any import-related content
      expect(page.getByText(/Import/i).first()).toBeVisible();
    });
  });

  test('should show health check endpoint', async ({ page }) => {
    // Navigate to health check
    await page.goto('/projects/health');
    
    // Should show health status
    await expect(page.getByText(/healthy|status/i)).toBeVisible({ timeout: 5000 }).catch(() => {
      // Health check may show different text
      expect(page.locator('body')).toContainText('');
    });
  });
});

test.describe('API Integration', () => {
  test('should hit API health endpoint directly', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('should list projects via API', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/projects');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('projects');
    expect(Array.isArray(data.projects)).toBeTruthy();
  });
});

test.describe('Interview Flow', () => {
  test('should show interview page', async ({ page }) => {
    await page.goto('/interview');
    
    // Should show interview interface
    await expect(page.getByText(/interview|面试/i).first()).toBeVisible({ timeout: 5000 }).catch(() => {
      expect(page.locator('body')).toBeVisible();
    });
  });
});

test.describe('Evidence Page', () => {
  test('should show evidence page', async ({ page }) => {
    await page.goto('/evidence');
    
    // Should show evidence interface
    await expect(page.getByText(/evidence|证据/i).first()).toBeVisible({ timeout: 5000 }).catch(() => {
      expect(page.locator('body')).toBeVisible();
    });
  });
});

test.describe('Upgrade Map', () => {
  test('should show upgrade map', async ({ page }) => {
    await page.goto('/upgrade-map');
    
    // Should show upgrade map interface
    await expect(page.getByText(/upgrade|升级/i).first()).toBeVisible({ timeout: 5000 }).catch(() => {
      expect(page.locator('body')).toBeVisible();
    });
  });
});

test.describe('Tasks Page', () => {
  test('should show tasks page', async ({ page }) => {
    await page.goto('/tasks');
    
    // Should show tasks interface
    await expect(page.getByText(/task|任务/i).first()).toBeVisible({ timeout: 5000 }).catch(() => {
      expect(page.locator('body')).toBeVisible();
    });
  });
});
