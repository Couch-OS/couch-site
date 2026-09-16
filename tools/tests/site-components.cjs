// Exercise local documentation fixtures and the one-shot homepage headline.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const os = require('node:os');
const base = process.env.SITE_URL || 'http://127.0.0.1:8098/';
(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    for (const width of [1440, 1000, 850, 390, 320]) {
      await page.setViewportSize({width, height:1000});
      await page.goto(new URL('developers/components.html', base).href);
      const preview = page.locator('[data-component-previews]');
      assert.equal(await preview.locator('.component-preview-card').count(), 4);
      await preview.getByRole('button', {name:'Volume up', exact:true}).click();
      assert.equal(await preview.locator('[data-volume-status]').textContent(), '40%');
      await preview.getByRole('button', {name:'Volume down', exact:true}).click();
      assert.equal(await preview.locator('[data-volume-status]').textContent(), '35%');
      await preview.getByRole('button', {name:'Turn off', exact:true}).click();
      assert.equal(await preview.getByRole('button', {name:'Turn on', exact:true}).count(), 1);
      await preview.getByLabel('Source', {exact:true}).selectOption('hdmi2');
      assert.match(await preview.getByRole('status').textContent(), /input:hdmi2/);
      await preview.getByRole('button', {name:'Refresh inputs', exact:true}).click();
      assert.match(await preview.getByRole('status').textContent(), /inputs refreshed/);
      await preview.getByRole('button', {name:'Reset demo', exact:true}).click();
      assert.equal(await preview.getByRole('button', {name:'Turn off', exact:true}).count(), 1);
      assert.equal(await preview.getByLabel('Source', {exact:true}).inputValue(), '');
      for (const details of await preview.locator('details').all()) {
        await details.locator('summary').click();
        const declaration = JSON.parse(await details.locator('code').textContent());
        assert.ok(['command_group','status_text','toggle','input_selector'].includes(declaration.kind));
      }
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `previews overflow at ${width}`);
      if ([1440,390].includes(width)) {
        await preview.screenshot({path:path.join(os.tmpdir(), `couch-components-${width}.png`)});
      }
    }
    // Bound volume and keep keyboard activation equivalent to clicking.
    await page.locator('[data-volume="5"]').evaluate(button => {for(let i=0;i<30;i++) button.click()});
    assert.equal(await page.locator('[data-volume-status]').textContent(), '100%');
    await page.locator('[data-volume="-5"]').evaluate(button => {for(let i=0;i<30;i++) button.click()});
    assert.equal(await page.locator('[data-volume-status]').textContent(), '0%');
    await page.locator('[data-power]').focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('[data-power]').textContent(), 'Turn on');

    // Suppress the unrelated on-demand WASM demo while checking the headline.
    await page.route('**/demo.js', route => route.fulfill({body:'',contentType:'application/javascript'}));
    for (const width of [1440, 1000, 850, 390, 320]) {
      await page.setViewportSize({width, height:1000});
      await page.goto(base);
      await page.waitForSelector('.headline-rolling');
      const box = await page.locator('#headline').boundingBox();
      assert.equal(await page.locator('.headline-word').count(), 16);
      assert.match(await page.locator('#headline').ariaSnapshot(), /Linux for your universal remote\./);
      const fits = await page.locator('.headline-word').evaluateAll(lines => lines.every(line => line.scrollWidth <= line.clientWidth + 1));
      assert.equal(fits, true, `headline names fit at ${width}`);
      await page.locator('.headline-track').evaluate(track => track.getAnimations()[0].finish());
      await page.waitForSelector('.headline-reel', {state:'detached'});
      assert.equal(await page.locator('#headline em').textContent(), 'universal remote.');
      assert.deepEqual(await page.locator('#headline').boundingBox(), box, `headline has no layout shift at ${width}`);
    }
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.goto(base);
    await page.evaluate(() => document.fonts.ready);
    assert.equal(await page.locator('.headline-reel').count(), 0);
    assert.equal(await page.locator('#headline em').textContent(), 'universal remote.');
    assert.deepEqual(errors, []);
    console.log('PASS: four interactive component previews, declarations, keyboard controls, responsive layouts, headline sequence and reduced motion.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error);process.exit(1)});
