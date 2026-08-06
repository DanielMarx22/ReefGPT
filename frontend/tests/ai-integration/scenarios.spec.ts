import { test, expect } from '@playwright/test';

// Use fully serial execution so we don't spam the LLM API concurrently and hit rate limits instantly.
test.describe.configure({ mode: 'serial' });

test.describe('Real AI Diagnostics Regression Tests', () => {
  // LLM responses can take a bit, so allow 60s per test
  test.setTimeout(60000);

  const scenarios = [
    {
      name: 'Scenario 1: Alkalinity & Calcium Spike',
      bypassButton: /Customer A/i,
      prompt: 'Why do my LPS corals look shrunk today?',
      expectedRegex: /alkalinity/i
    },
    {
      name: 'Scenario 2: Amino Acid Overdose',
      bypassButton: /Customer B/i,
      prompt: 'Why are my mushroom colonies turning white slowly?',
      expectedRegex: /amino|toxicity|lighting/i
    },
    {
      name: 'Scenario 3: Rogue Fish Aggression',
      bypassButton: /Customer C/i,
      prompt: 'Why do the fins on my newest angelfish look torn up?',
      expectedRegex: /clown|niger|trigger|aggression/i
    },
    {
      name: 'Scenario 4: Heater Failure (Temp Drop)',
      bypassButton: /Customer D/i,
      prompt: 'Why are all my corals shrunk up and fish hiding?',
      expectedRegex: /temperature|temp|heater/i
    },
    {
      name: 'Scenario 5: Alk Depletion (Reactor Clog)',
      bypassButton: /Customer E/i,
      prompt: 'Why are my SPS corals shrunk so much today?',
      expectedRegex: /alkalinity|calcium|reactor|clog/i
    }
  ];

  for (const scenario of scenarios) {
    test(`Accurately diagnoses ${scenario.name}`, async ({ page }) => {
      console.log(`\n======================================================`);
      console.log(`Testing: ${scenario.name}`);
      console.log(`======================================================`);
      
      // 1. Navigate and Login using the appropriate Developer Bypass
      await page.goto('/');
      await page.getByRole('button', { name: scenario.bypassButton }).click();

      // Ensure the chat input is visible, meaning login succeeded
      const chatInput = page.getByPlaceholder(/Ask ReefGPT/i);
      await expect(chatInput).toBeVisible();

      // Clear the chat to ensure a fresh session (just in case history lingered)
      const clearBtn = page.getByRole('button', { name: /Clear History/i });
      if (await clearBtn.isVisible()) {
        page.on('dialog', dialog => dialog.accept());
        await clearBtn.click();
        await expect(clearBtn).not.toBeVisible();
      }

      // 2. Ask the question
      await chatInput.fill(scenario.prompt);
      await chatInput.press('Enter');

      console.log(`Sent Prompt: "${scenario.prompt}"`);

      // 3. Wait for the AI's response to stream in
      // The frontend renders the AI response in a div containing "ReefGPT" as a label.
      // We want to wait for the network to finish the POST /chat-v2 request.
      const response = await page.waitForResponse(
        res => res.url().includes('/chat-v2') && res.request().method() === 'POST' && res.status() === 200,
        { timeout: 50000 }
      );
      
      const responseJson = await response.json();
      console.log(`AI Reply:\n${responseJson.reply}`);
      
      // 4. Verify accuracy based on expected keywords
      // First we check the raw API response
      expect(responseJson.reply).toMatch(scenario.expectedRegex);
      
      // And we verify that it actually rendered in the UI
      // We look for the newest AI message by finding the last message block
      // (This is a simplified check that looks for the AI response text anywhere on the page)
      // Since it's a dynamic stream, the exact full text might take a tiny bit to render
      // but waiting for the network response usually means React is right behind it.
      await page.waitForTimeout(1000); // Small buffer for React to render the final streamed text
      
      const fullText = await page.locator('body').innerText();
      expect(fullText).toMatch(scenario.expectedRegex);
      
      console.log(`✅ Passed: AI identified correct root cause (${scenario.expectedRegex})`);
    });
  }
});
