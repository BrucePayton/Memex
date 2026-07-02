const { test, expect } = require("@playwright/test");

test.describe("Memex dashboard schedules", () => {
  test("loads the schedules view and opens the new schedule form", async ({ page }) => {
    await page.goto("/");
    await page.waitForTimeout(2500);
    await page.evaluate(async () => {
      await window.showSchedules();
      await new Promise((resolve) => setTimeout(resolve, 300));
    });

    await expect(page.getByRole("heading", { name: /scheduled tasks|定时任务|스케줄된 작업/i })).toBeVisible();
    await page.waitForFunction(() => {
      const el = document.querySelector("#schedulesList");
      return !!el && el.textContent.trim().length > 0;
    });
    await page.evaluate(() => {
      window.showScheduleForm();
    });

    await page.waitForFunction(() => {
      const name = document.getElementById("schedName");
      const cron = document.getElementById("schedCron");
      const enabled = document.getElementById("schedEnabled");
      return !!name && !!cron && !!enabled;
    });

    const scheduleFormState = await page.evaluate(() => ({
      cron: document.getElementById("schedCron").value,
      enabled: document.getElementById("schedEnabled").checked,
    }));

    expect(scheduleFormState.cron).toBe("0 3 * * *");
    expect(scheduleFormState.enabled).toBe(true);
  });
});
