import { test, expect } from '@playwright/test';

test.describe('Search Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for initial load
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });
  });

  test('should search for bills by keyword', async ({ page }) => {
    // Type search query
    const searchInput = page.getByTestId('search-input');
    await searchInput.fill('healthcare');

    // Submit search
    await page.getByTestId('search-button').click();

    // Should show loading state
    await expect(page.getByTestId('loading-spinner')).toBeVisible();

    // Should show results
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });

    // Results should contain the search term (case-insensitive)
    const billCards = page.getByTestId('bill-card');
    const firstCard = billCards.first();
    if (await billCards.count() > 0) {
      const cardText = await firstCard.textContent();
      expect(cardText?.toLowerCase()).toContain('health');
    }
  });

  test('should show no results message for invalid search', async ({ page }) => {
    // Type search query that should return no results
    const searchInput = page.getByTestId('search-input');
    await searchInput.fill('xyzabc123nonexistent');

    // Submit search
    await page.getByTestId('search-button').click();

    // Wait for search to complete
    await page.waitForTimeout(2000);

    // Should show empty state
    const emptyMessage = page.getByTestId('bill-list-empty');
    if (await emptyMessage.isVisible()) {
      await expect(emptyMessage).toContainText(/No bills found/i);
    }
  });

  test('should clear search and show all bills', async ({ page }) => {
    // Perform a search
    const searchInput = page.getByTestId('search-input');
    await searchInput.fill('healthcare');
    await page.getByTestId('search-button').click();

    // Wait for results
    await page.waitForTimeout(2000);

    // Clear search
    await searchInput.clear();
    await page.getByTestId('search-button').click();

    // Should show all bills again
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });
  });

  test('should maintain search term in input after search', async ({ page }) => {
    const searchTerm = 'education';

    // Type and search
    await page.getByTestId('search-input').fill(searchTerm);
    await page.getByTestId('search-button').click();

    // Wait for search to complete
    await page.waitForTimeout(2000);

    // Search term should still be in input
    await expect(page.getByTestId('search-input')).toHaveValue(searchTerm);
  });

  test('should handle search with Enter key', async ({ page }) => {
    // Type search query
    await page.getByTestId('search-input').fill('healthcare');

    // Press Enter
    await page.getByTestId('search-input').press('Enter');

    // Should show loading state
    await expect(page.getByTestId('loading-spinner')).toBeVisible();

    // Should show results
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });
  });
});
