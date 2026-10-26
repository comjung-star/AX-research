const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function createHarness() {
  const elements = new Map();
  function control() {
    const events = new Map();
    return { addEventListener: (event, callback) => events.set(event, callback), trigger: (event, payload) => events.get(event)?.(payload) };
  }
  for (const [buttonId, dialogId] of [["architecture-button", "architecture-dialog"], ["paper-status-button", "paper-status-dialog"]]) {
    const closeButtons = [control(), control()];
    const dialog = Object.assign(control(), {
      open: false,
      showModal() { this.open = true; },
      close() { this.open = false; },
      querySelectorAll: () => closeButtons,
      getBoundingClientRect: () => ({ left: 20, right: 500, top: 20, bottom: 600 }),
      closeButtons
    });
    elements.set(buttonId, control());
    elements.set(dialogId, dialog);
  }
  const context = { document: { getElementById: (elementId) => elements.get(elementId) } };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../prototype/web/research.js"), "utf8"), context);
  return elements;
}

test("each research button opens only its own popup", () => {
  const elements = createHarness();
  elements.get("architecture-button").trigger("click");
  assert.equal(elements.get("architecture-dialog").open, true);
  assert.equal(elements.get("paper-status-dialog").open, false);
  elements.get("architecture-dialog").close();
  elements.get("paper-status-button").trigger("click");
  assert.equal(elements.get("paper-status-dialog").open, true);
  assert.equal(elements.get("architecture-dialog").open, false);
});

test("top and bottom close buttons both close each popup", () => {
  for (const dialogId of ["architecture-dialog", "paper-status-dialog"]) {
    const dialog = createHarness().get(dialogId);
    for (const button of dialog.closeButtons) {
      dialog.showModal();
      button.trigger("click");
      assert.equal(dialog.open, false);
    }
  }
});

test("backdrop closes the popup but content and scrollbar area do not", () => {
  const dialog = createHarness().get("architecture-dialog");
  dialog.showModal();
  dialog.trigger("click", { target: {}, clientX: 1, clientY: 1 });
  assert.equal(dialog.open, true);
  dialog.trigger("click", { target: dialog, clientX: 490, clientY: 300 });
  assert.equal(dialog.open, true);
  dialog.trigger("click", { target: dialog, clientX: 10, clientY: 300 });
  assert.equal(dialog.open, false);
});
