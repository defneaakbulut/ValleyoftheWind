const addSessionButton = document.querySelector("#addSessionButton");
const sessionFields = document.querySelector("#questSessionFields");

if (addSessionButton) {
  addSessionButton.addEventListener("click", function () {
    const firstSession = document.querySelector(".quest-session-row");
    const newSession = firstSession.cloneNode(true);
    const newRemoveButton = newSession.querySelector(".remove-session-button");

    newSession.querySelector("[name='txt_session_day']").value = "";
    newSession.querySelector("[name='txt_session_start_time']").value = "";
    newSession.querySelector("[name='txt_session_location']").value = "";
    newRemoveButton.hidden = false;
    newRemoveButton.addEventListener("click", removeSession);

    sessionFields.appendChild(newSession);

    const removeButtons = document.querySelectorAll(".remove-session-button");
    for (const button of removeButtons) {
      button.hidden = false;
    }
  });
}

if (sessionFields) {
  const removeButtons = document.querySelectorAll(".remove-session-button");

  for (const button of removeButtons) {
    button.addEventListener("click", removeSession);
  }
}

function removeSession(event) {
  const removeButton = event.currentTarget;
  removeButton.parentElement.parentElement.remove();

  const sessionRows = document.querySelectorAll(".quest-session-row");
  const removeButtons = document.querySelectorAll(".remove-session-button");

  if (sessionRows.length === 1) {
    removeButtons[0].hidden = true;
  }
}

const filters = document.querySelector("#questFilters");
const cards = document.querySelectorAll(".quest-session-card");
const noMatchesMessage = document.querySelector("#noQuestMatches");

if (filters) {
  filters.addEventListener("change", function () {
    const selectedDay = document.querySelector("#filterDay").value;
    const selectedQuestType = document.querySelector("#filterQuestType").value;
    const selectedDifficulty = document.querySelector("#filterDifficulty").value;
    const selectedRole = document.querySelector("#filterRole").value;
    let visibleQuests = 0;

    for (const card of cards) {
      const matchesDay = selectedDay === "" || card.dataset.day === selectedDay;
      const matchesQuestType = selectedQuestType === "" || card.dataset.questType === selectedQuestType;
      const matchesDifficulty = selectedDifficulty === "" || card.dataset.difficulty === selectedDifficulty;
      const matchesRole = selectedRole === "" || !card.dataset.takenRoles.includes(selectedRole);

      if (matchesDay && matchesQuestType && matchesDifficulty && matchesRole) {
        card.hidden = false;
        visibleQuests += 1;
      } else {
        card.hidden = true;
      }
    }
    if (noMatchesMessage) {
      noMatchesMessage.hidden = visibleQuests > 0;
    }
  });
}
