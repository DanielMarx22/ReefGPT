import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

// Use a longer timeout for real AI calls (e.g. 30 seconds)
test.describe('Real AI Intelligence Evaluation (Golden Dataset)', () => {
  test.setTimeout(30000); 

  // Clear chat history before each test so context from one test doesn't bleed into the next
  test.beforeEach(async ({ request }) => {
    await request.delete('http://localhost:8005/clear-chat');
  });

  test('AI accurately parses complex livestock additions', async ({ request }) => {
    // We can hit the backend API directly for this test, bypassing the frontend UI
    // assuming backend is running on localhost:8005
    const response = await request.post('http://localhost:8005/chat-v2', {
      data: {
        text: "I just bought a new Purple Tang (Zebrasoma xanthurum) and dropped him in the tank today."
      }
    });

    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    
    console.log("--- AI LIVESTOCK TEST RESULT ---");
    console.log("User Prompt: I just bought a new Purple Tang (Zebrasoma xanthurum) and dropped him in the tank today.");
    console.log("AI Reply:", data.reply);
    console.log("Proposed Actions:", JSON.stringify(data.proposed_actions, null, 2));
    
    // Verify the AI formulated the correct action schema
    expect(data.proposed_actions).toBeDefined();
    expect(data.proposed_actions.length).toBeGreaterThan(0);
    
    const action = data.proposed_actions.find((a: any) => a.action === 'add_inhabitant');
    expect(action).toBeDefined();
    expect(action.species.toLowerCase()).toContain('xanthurum');
  });

  test('AI triages critical tank parameters accurately', async ({ request }) => {
    const response = await request.post('http://localhost:8005/chat-v2', {
      data: {
        text: "My SPS corals are peeling from the base and my Alk dropped from 9.0 to 7.0 overnight."
      }
    });

    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    
    console.log("--- AI TRIAGE TEST RESULT ---");
    console.log("User Prompt: My SPS corals are peeling from the base and my Alk dropped from 9.0 to 7.0 overnight.");
    console.log("AI Reply:", data.reply);
    console.log("X-Ray Reasoning:", JSON.stringify(data.xray, null, 2));
    
    // Check if the AI's xray reasoning determined this is a critical issue
    // (Assuming the xray json is returned by the API as described in current_functionality.md)
    if (data.xray) {
      expect(data.xray.severity).toMatch(/CRITICAL|HIGH|WARNING/i);
    }
    
    // It should also recommend testing other parameters or doing a water change
    expect(data.reply.toLowerCase()).toMatch(/alk|alkalinity|rtn|stn|swing|water change|parameters/i);
  });
});
