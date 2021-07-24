$(document).ready(function () {
  tippy.delegate('body', {
    target: '[data-tippy-content]'
  });

  $(document).on('input', 'input[type="search"]', function () {
    /**
     * @type {string}
     */
    const value = $(this).val().toLowerCase();
    const wavs = {
      'nino': 'nino.wav',
      'abi': 'nino.wav',
      'priestess': 'nino.wav',
      'sonia': 'sonia.wav',
      'trash': 'sonia.wav',
      'garbage': 'sonia.wav',
      'hector': 'hector.wav',
      'bector': 'hector.wav',
      'sharena': 'sharena.wav',
      'rein': 'magic.wav',
      'linus': 'linus.wav',
      'raven': 'linus.wav',
      'poro': 'oliver.wav',
      'oliver': 'oliver.wav',
      'ike': 'ike.wav',
      'bike': 'ike.wav',
    };

    if (value in wavs) {
      playWav(wavs[value]);
    }
  });
});
