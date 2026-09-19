/**
 * Playwright E2E Test: Frontend Page Validation
 * 
 * Tests that all frontend pages load correctly
 */

import { test, expect } from '@playwright/test';

test.describe('Frontend Pages', () => {
  test('should load the home page', async ({ page }) => {
    await page.goto('/');
    // Page should load without error
    await expect(page.locator('body')).toBeVisible();
  });

  test('should load interview page', async ({ page }) => {
    await page.goto('/interview');
    await expect(page.locator('body')).toBeVisible();
  });

  test('should load evidence page', async ({ page }) => {
    await page.goto('/evidence');
    await expect(page.locator('body')).toBeVisible();
  });

  test('should load upgrade map page', async ({ page }) => {
    await page.goto('/upgrade-map');
    await expect(page.locator('body')).toBeVisible();
  });

  test('should load tasks page', async ({ page }) => {
    await page.goto('/tasks');
    await expect(page.locator('body')).toBeVisible();
  });

  test('should load projects import page', async ({ page }) => {
    await page.goto('/projects/import');
    await expect(page.locator('body')).toBeVisible();
  });

  test('should load projects health page', async ({ page }) => {
    await page.goto('/projects/health');
    await expect(page.locator('body')).toBeVisible();
  });
});
