(() => {
  const input = document.querySelector("[data-developer-search]");
  if (!input) return;
  const cards = [...document.querySelectorAll("[data-search-value]")];
  const status = document.querySelector("[data-search-status]");
  const update = () => {
    const words = input.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const card of cards) {
      const match = words.every((word) => card.dataset.searchValue.includes(word));
      card.hidden = !match;
      if (match) shown += 1;
    }
    status.textContent = words.length ? `${shown} topic${shown === 1 ? "" : "s"} found` : "";
  };
  input.addEventListener("input", update);
})();
