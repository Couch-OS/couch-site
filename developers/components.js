// Local documentation fixtures. No device discovery, requests or commands.
(() => {
  const root = document.querySelector('[data-component-previews]');
  if (!root) return;
  const volumeStatus = root.querySelector('[data-volume-status]');
  const powerButton = root.querySelector('[data-power]');
  const input = root.querySelector('[data-input]');
  const feedback = root.querySelector('[data-preview-status]');
  let volume = 35;
  let power = true;
  const render = () => {
    volumeStatus.textContent = `${volume}%`;
    powerButton.textContent = power ? 'Turn off' : 'Turn on';
  };
  root.querySelectorAll('[data-volume]').forEach(button => {
    button.addEventListener('click', () => {
      volume = Math.max(0, Math.min(100, volume + Number(button.dataset.volume)));
      render();
      feedback.textContent = `Sample command: ${Number(button.dataset.volume) > 0 ? 'volume-up' : 'volume-down'}. Volume ${volume}%.`;
    });
  });
  powerButton.addEventListener('click', () => {
    power = !power;
    render();
    feedback.textContent = `Sample command: power-${power ? 'on' : 'off'}. Power ${power ? 'on' : 'off'}.`;
  });
  input.addEventListener('change', () => {
    feedback.textContent = input.value
      ? `Sample command: input:${input.value}. Source ${input.selectedOptions[0].textContent}.`
      : 'Choose a sample input.';
  });
  root.querySelector('[data-refresh-inputs]').addEventListener('click', () => {
    feedback.textContent = 'Sample inputs refreshed: HDMI 1, HDMI 2 and Bluetooth.';
  });
  root.querySelector('[data-preview-reset]').addEventListener('click', () => {
    volume = 35;
    power = true;
    input.value = '';
    render();
    feedback.textContent = 'Sample receiver ready. Volume 35%; power on.';
  });
})();
