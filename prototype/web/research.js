"use strict";

function setupResearchDialog(buttonId, dialogId) {
  const button = document.getElementById(buttonId);
  const dialog = document.getElementById(dialogId);
  button.addEventListener("click", () => dialog.showModal());
  dialog.querySelectorAll("[data-close-dialog]").forEach((closeButton) => {
    closeButton.addEventListener("click", () => dialog.close());
  });
  dialog.addEventListener("click", (event) => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
}

setupResearchDialog("architecture-button", "architecture-dialog");
setupResearchDialog("paper-status-button", "paper-status-dialog");
