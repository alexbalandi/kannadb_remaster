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
