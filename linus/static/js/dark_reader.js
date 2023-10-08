document.addEventListener("DOMContentLoaded", function () {
  const toggleButton = document.getElementById("darkModeToggle");
  const body = document.body;

  function enableDarkMode() {
    //body.classList.add("dark-mode");
    DarkReader.enable({
      brightness: 100,
      contrast: 90,
      sepia: 10,
    });
  }

  function disableDarkMode() {
    //body.classList.remove("dark-mode");
    DarkReader.disable();
  }

  // Check the state flag in local storage on initial load
  if (localStorage.getItem("darkMode") === "enabled") {
    enableDarkMode();
  } else if (
    localStorage.getItem("darkMode") === null &&
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    // If no state flag in local storage, check for the OS preference
    enableDarkMode();
    localStorage.setItem("darkMode", "enabled");
  } else {
    disableDarkMode();
  }

  if (toggleButton) {
    // Handle the button click event
    toggleButton.addEventListener("click", () => {
      if (localStorage.getItem("darkMode") === "enabled") {
        disableDarkMode();
        localStorage.setItem("darkMode", "disabled");
      } else {
        enableDarkMode();
        localStorage.setItem("darkMode", "enabled");
      }
    });
  }
});
