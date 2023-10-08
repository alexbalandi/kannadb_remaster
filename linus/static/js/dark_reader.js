document.addEventListener("DOMContentLoaded", function () {
  const toggleButton = document.getElementById("darkModeToggle");
  const body = document.body;
  if (
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    DarkReader.enable({
      brightness: 100,
      contrast: 90,
      sepia: 10,
    });
  }

  if (toggleButton) {
    // Check if the button exists
    toggleButton.addEventListener("click", () => {
      if (body.classList.contains("dark-mode")) {
        body.classList.remove("dark-mode");
        DarkReader.disable();
      } else {
        body.classList.add("dark-mode");
        DarkReader.enable({
          brightness: 100,
          contrast: 90,
          sepia: 10,
        });
      }
    });
  }
});
