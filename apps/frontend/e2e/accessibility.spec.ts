import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility', () => {
  test('homepage should not have automatically detectable accessibility issues', async ({ page }) => {
    await page.goto('/');

    // Wait for page to load
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('bill detail page should not have automatically detectable accessibility issues', async ({ page }) => {
    // Navigate to bill detail
    await page.goto('/');
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });
    await page.getByTestId('bill-card-link').first().click();
    await expect(page.getByTestId('bill-detail-view')).toBeVisible({ timeout: 10000 });

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should support keyboard navigation on homepage', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });

    // Tab to search input
    await page.keyboard.press('Tab');
    await expect(page.getByTestId('search-input')).toBeFocused();

    // Tab to search button
    await page.keyboard.press('Tab');
    await expect(page.getByTestId('search-button')).toBeFocused();
  });

  test('should support keyboard navigation in pagination', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('bill-list')).toBeVisible({ timeout: 10000 });

    // Find and focus the "Next" button
    const nextButton = page.getByTestId('pagination-next');
    await nextButton.focus();

    // Press Enter
    await page.keyboard.press('Enter');

    // Should navigate to page 2
    await expect(page.getByTestId('pagination-current')).toContainText('Page 2');
  });

  test('loading spinner should have proper aria attributes', async ({ page }) => {
    await page.goto('/');

    const spinner = page.getByTestId('loading-spinner');

    // Check for aria attributes
    await expect(spinner).toHaveAttribute('role', 'status');
    await expect(spinner).toHaveAttribute('aria-live', 'polite');
  });

  test('error alert should have proper aria attributes', async ({ page }) => {
    // Navigate to non-existent bill to trigger error
    await page.goto('/bills/999/hr/99999');

    const errorAlert = page.getByTestId('error-alert');
    await expect(errorAlert).toBeVisible({ timeout: 10000 });

    // Check for aria attributes
    await expect(errorAlert).toHaveAttribute('role', 'alert');
  });
});
