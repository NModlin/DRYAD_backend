import { test, expect } from '@playwright/test';

test.describe('Dryads Console Chat Interface', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the chat interface
    await page.goto('http://localhost:3001');
  });

  test('should load the chat interface successfully', async ({ page }) => {
    // Check if the main chat interface is loaded
    await expect(page.locator('h1:has-text("Dryads Console")')).toBeVisible();
    await expect(page.locator('p:has-text("Unified chat interface for DRYAD.AI")')).toBeVisible();
    
    // Check if the welcome message is displayed
    await expect(page.locator('text=Welcome to The Dryads Console!')).toBeVisible();
    
    // Check if quick actions are available
    await expect(page.locator('button:has-text("Explore Groves")')).toBeVisible();
    await expect(page.locator('button:has-text("Consult Oracle")')).toBeVisible();
    await expect(page.locator('button:has-text("Search Memories")')).toBeVisible();
  });

  test('should display command suggestions when typing', async ({ page }) => {
    // Type in the chat input
    const input = page.locator('textarea[placeholder*="Ask about your groves"]');
    await input.fill('grove');
    
    // Check if command suggestions appear
    await expect(page.locator('button:has-text("Explore my groves")')).toBeVisible();
    await expect(page.locator('div:has-text("Navigate through your knowledge trees")')).toBeVisible();
  });

  test('should send a message and receive a response', async ({ page }) => {
    // Send a message
    const input = page.locator('textarea[placeholder*="Ask about your groves"]');
    await input.fill('show groves');
    await page.click('button:has-text("Send")');
    
    // Check if the message is sent
    await expect(page.locator('text=You').first()).toBeVisible();
    await expect(page.locator('text=show groves')).toBeVisible();
    
    // Check if system response appears
    await expect(page.locator('text=Dryads Console')).toBeVisible();
    await expect(page.locator('text=I found')).toBeVisible();
  });

  test('should handle session management', async ({ page }) => {
    // Click on the history button to open session panel
    await page.click('button[title="Manage Conversations"]');
    
    // Check if session panel is visible
    await expect(page.locator('text=Conversations')).toBeVisible();
    
    // Check if default session exists
    await expect(page.locator('text=Main Conversation')).toBeVisible();
    
    // Create a new session
    await page.click('button[title="New Conversation"]');
    
    // Check if new session is created
    await expect(page.locator('text=Conversation 2')).toBeVisible();
  });

  test('should toggle context panel', async ({ page }) => {
    // Check if context panel is visible by default
    await expect(page.locator('h3:has-text("Current Context")')).toBeVisible();
    
    // Toggle context panel
    await page.click('button[title="Toggle Context Panel"]');
    
    // Check if context panel is hidden
    await expect(page.locator('text=Current Context')).not.toBeVisible();
  });

  test('should handle quick action buttons', async ({ page }) => {
    // Click on quick action buttons
    await page.click('button:has-text("Explore Groves")');
    
    // Check if the command is processed
    await expect(page.locator('text=You').first()).toBeVisible();
    await expect(page.locator('text=explore my groves')).toBeVisible();
    
    // Check if system response appears
    await expect(page.locator('text=Dryads Console')).toBeVisible();
  });

  test('should display quantum-inspired animations', async ({ page }) => {
    // Check if quantum-inspired elements are present
    const chatContainer = page.locator('div[class*="chat"]').first();
    await expect(chatContainer).toBeVisible();
    
    // Send a message to trigger loading state
    const input = page.locator('textarea[placeholder*="Ask about your groves"]');
    await input.fill('test message');
    await page.click('button:has-text("Send")');
    
    // Check if loading animation appears
    await expect(page.locator('text=Thinking')).toBeVisible();
    await expect(page.locator('.thinking-dots')).toBeVisible();
  });

  test('should handle keyboard shortcuts', async ({ page }) => {
    // Test Enter key to send message
    const input = page.locator('textarea[placeholder*="Ask about your groves"]');
    await input.fill('test message with enter');
    await input.press('Enter');
    
    // Check if message is sent
    await expect(page.locator('text=test message with enter')).toBeVisible();
    
    // Test Shift+Enter for new line
    await input.fill('first line');
    await input.press('Shift+Enter');
    await input.fill('second line');
    await input.press('Enter');
    
    // Check if multiline message is sent
    await expect(page.locator('text=first line')).toBeVisible();
    await expect(page.locator('text=second line')).toBeVisible();
  });
});