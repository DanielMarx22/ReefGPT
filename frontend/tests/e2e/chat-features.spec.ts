import { test, expect } from '@playwright/test';

test.describe('Chatbot Diagnostics & Features (Mocked API)', () => {
  
  test('Clear Chat History button works', async ({ page }) => {
    // Navigate to Dashboard
    await page.goto('/');
    
    // Login using Dev Bypass
    await page.getByRole('button', { name: /Customer A/i }).click();

    // Type in the chat and submit (don't need to mock since we just want to create a local message)
    const chatInput = page.getByPlaceholder(/Ask ReefGPT/i);
    await expect(chatInput).toBeVisible();
    await chatInput.fill('Hello ReefGPT');
    await chatInput.press('Enter');

    // Verify user message appears
    await expect(page.getByText('Hello ReefGPT', { exact: false })).toBeVisible();

    // Verify Clear History button appears
    const clearButton = page.getByRole('button', { name: /Clear History/i });
    await expect(clearButton).toBeVisible();

    // Handle window.confirm dialogue to accept
    page.on('dialog', dialog => dialog.accept());

    // Click it
    await clearButton.click();

    // Verify chat is cleared
    await expect(page.getByText('Hello ReefGPT', { exact: false })).not.toBeVisible();
    await expect(clearButton).not.toBeVisible();
  });

  test('Diagnoses Scenario 1 (Alkalinity Spike) correctly', async ({ page }) => {
    // Mock the Chat API
    await page.route('**/chat-v2*', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            reply: "The massive alkalinity spike in your tank is causing stress to your corals.",
            proposed_actions: [],
            debug_xray: {
              internal_thoughts: "The telemetry subagent caught an alkalinity spike of 12.2.",
              severity: "CRITICAL"
            }
          })
        });
      } else {
        await route.continue();
      }
    });

    await page.goto('/');
    
    // Login using Dev Bypass
    await page.getByRole('button', { name: /Customer A/i }).click();

    const chatInput = page.getByPlaceholder(/Ask ReefGPT/i);
    await chatInput.fill('Why are my corals shrunk today?');
    await chatInput.press('Enter');

    // Verify the AI response text appears
    await expect(page.getByText('The massive alkalinity spike', { exact: false })).toBeVisible();

    // Wait for and verify the X-Ray debug panel
    // Based on the UI, it's usually a collapsible section or raw JSON if X-Ray is open.
    // Let's just look for the internal thoughts text
    const xrayToggle = page.getByRole('button', { name: /Agent X-Ray/i });
    if (await xrayToggle.isVisible()) {
      await xrayToggle.click();
    }
    await expect(page.getByText('The telemetry subagent caught an alkalinity spike of 12.2.', { exact: false })).toBeVisible();
  });

  test('Adds a fish and edits equipment via chatbox actions', async ({ page }) => {
    // Mock the Chat API to return both add and edit actions
    await page.route('**/chat-v2*', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            reply: "I've queued up the addition of your Flame Angelfish and updated your heater notes.",
            proposed_actions: [
              {
                action: "add_inhabitant",
                name: "Flame Angelfish",
                species: "Centropyge loricula",
                category: "Fish"
              },
              {
                action: "update_inhabitant",
                id: 123,
                name: "300W Heater",
                notes: "Heater failed on Aug 5"
              }
            ]
          })
        });
      } else {
        await route.continue();
      }
    });

    // Mock the action execution APIs
    await page.route('**/add-inhabitant*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
    });
    await page.route('**/patch-inhabitant/*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
    });

    await page.goto('/');
    
    // Login using Dev Bypass
    await page.getByRole('button', { name: /Customer A/i }).click();

    const chatInput = page.getByPlaceholder(/Ask ReefGPT/i);
    await chatInput.fill('I bought a Flame Angel and my heater broke.');
    await chatInput.press('Enter');

    // Verify AI response
    await expect(page.getByText("I've queued up the addition", { exact: false })).toBeVisible();

    // Verify Action Popup
    const confirmBtn = page.getByRole('button', { name: /Confirm/i });
    await expect(confirmBtn).toBeVisible();
    
    // Verify the action items are displayed in the UI before confirming
    await expect(page.getByText('Flame Angelfish', { exact: false }).first()).toBeVisible();
    await expect(page.getByText('Heater failed', { exact: false }).first()).toBeVisible();

    await confirmBtn.click();
    
    // Popup should disappear
    await expect(confirmBtn).not.toBeVisible();
  });
});
