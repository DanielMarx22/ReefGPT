# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ai-integration\ai-accuracy.spec.ts >> Real AI Intelligence Evaluation (Golden Dataset) >> AI triages critical tank parameters accurately
- Location: tests\ai-integration\ai-accuracy.spec.ts:41:7

# Error details

```
Error: expect(received).toBeTruthy()

Received: false
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe.configure({ mode: 'serial' });
  4  | 
  5  | // Use a longer timeout for real AI calls (e.g. 30 seconds)
  6  | test.describe('Real AI Intelligence Evaluation (Golden Dataset)', () => {
  7  |   test.setTimeout(30000); 
  8  | 
  9  |   // Clear chat history before each test so context from one test doesn't bleed into the next
  10 |   test.beforeEach(async ({ request }) => {
  11 |     await request.delete('http://localhost:8005/clear-chat');
  12 |   });
  13 | 
  14 |   test('AI accurately parses complex livestock additions', async ({ request }) => {
  15 |     // We can hit the backend API directly for this test, bypassing the frontend UI
  16 |     // assuming backend is running on localhost:8005
  17 |     const response = await request.post('http://localhost:8005/chat-v2', {
  18 |       data: {
  19 |         text: "I just bought a new Purple Tang (Zebrasoma xanthurum) and dropped him in the tank today."
  20 |       }
  21 |     });
  22 | 
  23 |     expect(response.ok()).toBeTruthy();
  24 |     
  25 |     const data = await response.json();
  26 |     
  27 |     console.log("--- AI LIVESTOCK TEST RESULT ---");
  28 |     console.log("User Prompt: I just bought a new Purple Tang (Zebrasoma xanthurum) and dropped him in the tank today.");
  29 |     console.log("AI Reply:", data.reply);
  30 |     console.log("Proposed Actions:", JSON.stringify(data.proposed_actions, null, 2));
  31 |     
  32 |     // Verify the AI formulated the correct action schema
  33 |     expect(data.proposed_actions).toBeDefined();
  34 |     expect(data.proposed_actions.length).toBeGreaterThan(0);
  35 |     
  36 |     const action = data.proposed_actions.find((a: any) => a.action === 'add_inhabitant');
  37 |     expect(action).toBeDefined();
  38 |     expect(action.species.toLowerCase()).toContain('xanthurum');
  39 |   });
  40 | 
  41 |   test('AI triages critical tank parameters accurately', async ({ request }) => {
  42 |     const response = await request.post('http://localhost:8005/chat-v2', {
  43 |       data: {
  44 |         text: "My SPS corals are peeling from the base and my Alk dropped from 9.0 to 7.0 overnight."
  45 |       }
  46 |     });
  47 | 
> 48 |     expect(response.ok()).toBeTruthy();
     |                           ^ Error: expect(received).toBeTruthy()
  49 |     
  50 |     const data = await response.json();
  51 |     
  52 |     console.log("--- AI TRIAGE TEST RESULT ---");
  53 |     console.log("User Prompt: My SPS corals are peeling from the base and my Alk dropped from 9.0 to 7.0 overnight.");
  54 |     console.log("AI Reply:", data.reply);
  55 |     console.log("X-Ray Reasoning:", JSON.stringify(data.xray, null, 2));
  56 |     
  57 |     // Check if the AI's xray reasoning determined this is a critical issue
  58 |     // (Assuming the xray json is returned by the API as described in current_functionality.md)
  59 |     if (data.xray) {
  60 |       expect(data.xray.severity).toMatch(/CRITICAL|HIGH|WARNING/i);
  61 |     }
  62 |     
  63 |     // It should also recommend testing other parameters or doing a water change
  64 |     expect(data.reply.toLowerCase()).toMatch(/alk|alkalinity|rtn|stn|swing|water change|parameters/i);
  65 |   });
  66 | });
  67 | 
```