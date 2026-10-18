// Updates admission status without reloading the details page.

const statusForm = document.getElementById("status-form");
const statusSelect = document.getElementById("admission-status");
const statusNote = document.getElementById("status-note");
const statusBadge = document.getElementById("status-badge");

let savedStatus = statusSelect.value;

function showNote(message, isError) {
  statusNote.hidden = false;
  statusNote.textContent = message;
  statusNote.classList.toggle("is-error", isError);
}

statusForm.addEventListener("submit", function (event) {
  event.preventDefault();
});

statusSelect.addEventListener("change", async function () {
  const nextStatus = statusSelect.value;
  showNote("Saving...", false);

  try {
    const response = await fetch(statusForm.action, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ admission_status: nextStatus })
    });
    const result = await response.json();

    if (!response.ok || !result.ok) {
      statusSelect.value = savedStatus;
      showNote(result.message || "The status could not be saved.", true);
      return;
    }

    savedStatus = result.admission_status;
    statusBadge.textContent = result.admission_status;
    statusBadge.className = "status-badge status-" + result.admission_status.toLowerCase().replace(" ", "-");
    showNote("Admission status updated.", false);
  } catch (error) {
    statusSelect.value = savedStatus;
    showNote("The status could not be saved. Check your connection and try again.", true);
  }
});
