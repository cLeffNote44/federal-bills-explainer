import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display the homepage with header and search', async ({ page }) => {
    // Check header is visible
    await expect(page.getByRole('heading', { name: /Federal Bills Explainer/i })).toBeVisible();
    await expect(page.getByText(/Understanding US legislation made simple/i)).toBeVisible();

    // Check search bar is visible
    await expect(page.getByTestId('search-input')).toBeVisible();
    await expect(page.getByTestId('search-button')).toBeVisible();
  });

  test('should display loading state initially', async ({ page }) => {
    // Should show loading spinner
    await expect(page.getByTestId('loading-spinner')).toBeVisible();

    // Wait for bills to load
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });
  });

  test('should display bill cards when loaded', async ({ page }) => {
    // Wait for bills to load
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });

    // Should have at least one bill card
    const billCards = page.getByTestId('bill-card');
    await expect(billCards.first()).toBeVisible();

    // Bill card should have title and link
    const firstCard = billCards.first();
    await expect(firstCard.getByRole('heading')).toBeVisible();
    await expect(firstCard.getByTestId('bill-card-link')).toBeVisible();
  });

  test('should navigate to bill detail page when clicking a bill', async ({ page }) => {
    // Wait for bills to load
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });

    // Click the first bill's link
    const firstBillLink = page.getByTestId('bill-card-link').first();
    await firstBillLink.click();

    // Should navigate to bill detail page
    await expect(page).toHaveURL(/\/bills\/\d+\/[a-z]+\/\d+/);

    // Should show bill detail view
    await expect(page.getByTestId('bill-detail-view')).toBeVisible({ timeout: 10000 });
  });

  test('should show pagination controls', async ({ page }) => {
    // Wait for bills to load
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });

    // Check pagination is visible
    await expect(page.getByTestId('pagination')).toBeVisible();
    await expect(page.getByTestId('pagination-previous')).toBeVisible();
    await expect(page.getByTestId('pagination-next')).toBeVisible();
    await expect(page.getByTestId('pagination-current')).toContainText('Page 1');
  });

  test('should navigate through pages', async ({ page }) => {
    // Wait for bills to load
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });

    // Click next page
    await page.getByTestId('pagination-next').click();

    // Should show page 2
    await expect(page.getByTestId('pagination-current')).toContainText('Page 2');

    // Click previous page
    await page.getByTestId('pagination-previous').click();

    // Should show page 1 again
    await expect(page.getByTestId('pagination-current')).toContainText('Page 1');
  });
});
