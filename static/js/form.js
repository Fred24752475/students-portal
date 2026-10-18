// Loads faculty and department options from options.json, then keeps
// the department list in step with the faculty the student picks.

const facultySelect = document.getElementById("faculty");
const departmentSelect = document.getElementById("department");
const portalForm = document.getElementById("portal-form");
const formError = document.getElementById("form-error");

let faculties = [];

function fillSelect(select, values, placeholder) {
  select.innerHTML = "";

  const emptyOption = document.createElement("option");
  emptyOption.value = "";
  emptyOption.textContent = placeholder;
  select.appendChild(emptyOption);

  values.forEach(function (value) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
}

function departmentsFor(facultyName) {
  const faculty = faculties.find(function (item) {
    return item.name === facultyName;
  });

  return faculty ? faculty.departments : [];
}

function showDepartments(facultyName, selectedDepartment) {
  fillSelect(departmentSelect, departmentsFor(facultyName), "Select a department");
  if (selectedDepartment) {
    departmentSelect.value = selectedDepartment;
  }
}

async function loadOptions() {
  const response = await fetch("/static/data/options.json");
  const data = await response.json();
  faculties = data.faculties;

  fillSelect(
    facultySelect,
    faculties.map(function (faculty) {
      return faculty.name;
    }),
    "Select a faculty"
  );

  const savedFaculty = facultySelect.dataset.selected || "";
  const savedDepartment = departmentSelect.dataset.selected || "";

  if (savedFaculty) {
    facultySelect.value = savedFaculty;
    showDepartments(savedFaculty, savedDepartment);
  }
}

function fieldIsEmpty(field) {
  if (field.type === "radio") {
    const group = portalForm.querySelectorAll('input[name="' + field.name + '"]');
    return !Array.from(group).some(function (radio) {
      return radio.checked;
    });
  }

  if (field.type === "file") {
    return field.files.length === 0 && !field.dataset.existing;
  }

  return field.value.trim() === "";
}

function validateForm() {
  const fields = portalForm.querySelectorAll("input, select");
  let valid = true;
  const seenRadio = {};

  fields.forEach(function (field) {
    if (field.type === "radio") {
      if (seenRadio[field.name]) {
        return;
      }
      seenRadio[field.name] = true;
    }

    const empty = fieldIsEmpty(field);
    field.classList.toggle("is-invalid", empty && field.type !== "radio");

    if (field.type === "radio") {
      const group = portalForm.querySelectorAll('input[name="' + field.name + '"]');
      group.forEach(function (radio) {
        radio.classList.toggle("is-invalid", empty);
      });
    }

    if (empty) {
      valid = false;
    }
  });

  if (!valid) {
    formError.hidden = false;
    formError.textContent = "Fill in every field, including a photo, before submitting.";
  } else {
    formError.hidden = true;
    formError.textContent = "";
  }

  return valid;
}

facultySelect.addEventListener("change", function () {
  showDepartments(facultySelect.value, "");
});

portalForm.addEventListener("submit", function (event) {
  if (!validateForm()) {
    event.preventDefault();
  }
});

loadOptions();
