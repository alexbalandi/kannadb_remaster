/* Project specific Javascript goes here. */

sharena_wav_list_of_played_wavs = {};

playWav = function (wav_name) {
  if (!(wav_name in sharena_wav_list_of_played_wavs)) {
    sharena_wav_list_of_played_wavs[wav_name] = true;
    var audio = new Audio("/static/other/" + wav_name);
    audio.volume = 0.3;
    audio.play();
  }
};
