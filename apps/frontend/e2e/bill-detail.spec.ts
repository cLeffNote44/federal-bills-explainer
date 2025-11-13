import { test, expect } from '@playwright/test';

test.describe('Bill Detail Page', () => {
  test('should display bill details when navigating from homepage', async ({ page }) => {
    // Start at homepage
    await page.goto('/');

    // Wait for bills to load
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });

    // Click first bill
    await page.getByTestId('bill-card-link').first().click();

    // Should navigate to detail page
    await expect(page).toHaveURL(/\/bills\/\d+\/[a-z]+\/\d+/);

    // Should show loading state first
    await expect(page.getByTestId('loading-spinner')).toBeVisible();

    // Should show bill detail
    await expect(page.getByTestId('bill-detail-view')).toBeVisible({ timeout: 10000 });
  });

  test('should display bill header with back link', async ({ page }) => {
    // Navigate directly to a bill (using a common pattern)
    await page.goto('/');
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });
    await page.getByTestId('bill-card-link').first().click();

    // Wait for page load
    await expect(page.getByTestId('bill-detail-view')).toBeVisible({ timeout: 10000 });

    // Check header
    await expect(page.getByTestId('header')).toBeVisible();
    await expect(page.getByTestId('header-back-link')).toBeVisible();
    await expect(page.getByTestId('header-back-link')).toContainText(/Back to all bills/i);
  });

  test('should navigate back to homepage using back link', async ({ page }) => {
    // Navigate to a bill
    await page.goto('/');
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });
    await page.getByTestId('bill-card-link').first().click();

    // Wait for detail page
    await expect(page.getByTestId('bill-detail-view')).toBeVisible({ timeout: 10000 });

    // Click back link
    await page.getByTestId('header-back-link').click();

    // Should return to homepage
    await expect(page).toHaveURL('/');
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });
  });

  test('should display bill title and official information', async ({ page }) => {
    // Navigate to a bill
    await page.goto('/');
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });
    await page.getByTestId('bill-card-link').first().click();

    // Wait for detail page
    await expect(page.getByTestId('bill-detail-view')).toBeVisible({ timeout: 10000 });

    // Should have bill information
    await expect(page.getByRole('heading', { name: /Official Title/i })).toBeVisible();

    // Check for bill identifier in header
    const header = page.getByTestId('header');
    const headerText = await header.textContent();
    expect(headerText).toMatch(/[HS]R?-\d+/i); // Matches HR-123, S-456, etc.
  });

  test('should handle navigation with browser back button', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });

    // Navigate to bill detail
    await page.getByTestId('bill-card-link').first().click();
    await expect(page.getByTestId('bill-detail-view')).toBeVisible({ timeout: 10000 });

    // Use browser back button
    await page.goBack();

    // Should return to homepage
    await expect(page).toHaveURL('/');
    await expect(page.getByTestId('bill-list')).toBeVisible();
  });

  test('should handle direct URL navigation to bill detail', async ({ page }) => {
    // Try to navigate to a bill detail page directly
    // First, get a valid bill URL from the homepage
    await page.goto('/');
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });

    const firstLink = page.getByTestId('bill-card-link').first();
    const href = await firstLink.getAttribute('href');

    if (href) {
      // Navigate directly to that URL
      await page.goto(href);

      // Should load the bill detail
      await expect(page.getByTestId('bill-detail-view')).toBeVisible({ timeout: 10000 });
    }
  });

  test('should display error for non-existent bill', async ({ page }) => {
    // Navigate to a bill that doesn't exist
    await page.goto('/bills/999/hr/99999');

    // Should show error alert
    await expect(page.getByTestId('error-alert')).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId('error-alert')).toContainText(/not found|failed/i);

    // Should have back link
    await expect(page.getByText(/Back to all bills/i)).toBeVisible();
  });
});
