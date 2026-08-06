import { test, expect } from '@playwright/test';

test.describe('Basic UI Rendering & Navigation', () => {
  test('Navbar navigation works', async ({ page }) => {
    await page.goto('/');
    
    // Login using Dev Bypass
    await page.getByRole('button', { name: /Customer A/i }).click();
    
    // Verify the page loads successfully by looking for the chat input
    await expect(page.getByPlaceholder(/Ask ReefGPT/i)).toBeVisible();
    
    // Click on Livestock in the navbar
    await page.locator('a[href="/livestock"]').click();
    
    // Verify we navigated to the Livestock page
    await expect(page).toHaveURL(/.*livestock/);
    
    // Go back to Dashboard
    await page.getByRole('link', { name: /Dashboard/i }).click();
    await expect(page).toHaveURL('http://localhost:3000/');
  });

  test('Dashboard components render', async ({ page }) => {
    await page.goto('/');
    
    // Login using Dev Bypass
    await page.getByRole('button', { name: /Customer A/i }).click();
    
    // Check if the chat input exists
    await expect(page.getByPlaceholder(/Ask ReefGPT/i)).toBeVisible();
    
    // Check if the Readings panel exists
    await expect(page.getByRole('heading', { name: 'Log Parameters' })).toBeVisible();
    
    // Check if the DataView panel exists (Recent Readings)
    await expect(page.getByRole('heading', { name: 'Known Parameters' })).toBeVisible();
    
    // We expect at least one canvas (from Recharts) to be rendered for graphs
    // Wait for the data to load
    await page.waitForTimeout(1000); 
    // Recharts renders SVGs, let's look for an SVG with class 'recharts-surface'
    const graphSvg = page.locator('svg.recharts-surface').first();
    await expect(graphSvg).toBeVisible();
  });
});
