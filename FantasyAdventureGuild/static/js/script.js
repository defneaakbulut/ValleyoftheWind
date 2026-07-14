document.addEventListener("DOMContentLoaded", () => {
  const sessionFields = document.querySelector("#questSessionFields");
  const addSessionButton = document.querySelector("#addSessionButton");

  if (sessionFields && addSessionButton) {
    function updateSessionControls() {
      const rows = Array.from(sessionFields.querySelectorAll(".quest-session-row"));

      rows.forEach((row, index) => {
        const removeButton = row.querySelector(".remove-session-button");
        const dayField = row.querySelector("[name='txt_session_day']");
        const timeField = row.querySelector("[name='txt_session_start_time']");
        const locationField = row.querySelector("[name='txt_session_location']");

        [
          [dayField, "txt_session_day"],
          [timeField, "txt_session_start_time"],
          [locationField, "txt_session_location"],
        ].forEach(([field, baseId]) => {
          field.id = `${baseId}_${index + 1}`;
          field.closest(".form-field").querySelector("label").setAttribute("for", field.id);
        });

        removeButton.hidden = rows.length === 1;
      });
    }

    addSessionButton.addEventListener("click", () => {
      const firstRow = sessionFields.querySelector(".quest-session-row");
      const newRow = firstRow.cloneNode(true);

      newRow.querySelectorAll("select, input").forEach((field) => {
        field.value = "";
      });

      sessionFields.appendChild(newRow);
      updateSessionControls();
    });

    sessionFields.addEventListener("click", (event) => {
      const removeButton = event.target.closest(".remove-session-button");

      if (!removeButton) {
        return;
      }

      removeButton.closest(".quest-session-row").remove();
      updateSessionControls();
    });

    updateSessionControls();
  }

  const filters = document.querySelector("#questFilters");

  if (!filters) {
    return;
  }

  const dayFilter = document.querySelector("#filterDay");
  const questTypeFilter = document.querySelector("#filterQuestType");
  const difficultyFilter = document.querySelector("#filterDifficulty");
  const roleFilter = document.querySelector("#filterRole");
  const questCards = Array.from(document.querySelectorAll(".quest-session-card"));
  const noMatchesMessage = document.querySelector("#noQuestMatches");

  function roleIsAvailable(card, selectedRole) {
    if (!selectedRole) {
      return true;
    }

    const takenRoles = card.dataset.takenRoles
      .split(",")
      .map((role) => role.trim())
      .filter(Boolean);

    return !takenRoles.includes(selectedRole);
  }

  function applyQuestFilters() {
    const selectedDay = dayFilter.value;
    const selectedQuestType = questTypeFilter.value;
    const selectedDifficulty = difficultyFilter.value;
    const selectedRole = roleFilter.value;
    let visibleCount = 0;

    questCards.forEach((card) => {
      const matchesDay = !selectedDay || card.dataset.day === selectedDay;
      const matchesQuestType = !selectedQuestType || card.dataset.questType === selectedQuestType;
      const matchesDifficulty = !selectedDifficulty || card.dataset.difficulty === selectedDifficulty;
      const matchesRole = roleIsAvailable(card, selectedRole);
      const shouldShow = matchesDay && matchesQuestType && matchesDifficulty && matchesRole;

      card.hidden = !shouldShow;

      if (shouldShow) {
        visibleCount += 1;
      }
    });

    if (noMatchesMessage) {
      noMatchesMessage.hidden = visibleCount !== 0;
    }
  }

  filters.addEventListener("change", applyQuestFilters);
  filters.addEventListener("reset", () => {
    setTimeout(applyQuestFilters, 0);
  });

  applyQuestFilters();
});
