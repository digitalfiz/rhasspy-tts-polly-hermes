# Rhasspy Amazon Polly TTS Hermes MQTT Service

[![GitHub license](https://img.shields.io/github/license/digitalfiz/rhasspy-tts-polly-hermes.svg)](https://github.com/digitalfiz/rhasspy-tts-polly-hermes/blob/master/LICENSE)

Implements `hermes/tts` functionality from [Hermes protocol](https://docs.snips.ai/reference/hermes) using [Amazon Polly](https://docs.aws.amazon.com/polly/latest/dg/what-is.html).

See [documentation](https://rhasspy.readthedocs.io/en/latest/text-to-speech/#amazon-polly) for more details.

Use `--play-command aplay` to play speech locally instead of using `hermes/audioServer<siteId>/playBytes`.

## Installing

Clone the repository and create a virtual environment:

```bash
$ git clone https://github.com/digitalfiz/rhasspy-tts-polly-hermes.git
$ cd rhasspy-tts-polly-hermes
$ ./configure
$ make
$ make install
```

## Command-Line Options

```
usage: rhasspy-tts-polly-hermes [-h] --credentials CREDENTIALS --cache-dir CACHE_DIR [--voice VOICE] [--engine {standard,neural}] [--output-format {json,mp3,ogg_vorbis,pcm}] [--sample-rate SAMPLE_RATE]
                                [--language-code {arb,cmn-CN,cy-GB,da-DK,de-DE,en-AU,en-GB,en-GB-WLS,en-IN,en-US,es-ES,es-MX,es-US,fr-CA,fr-FR,is-IS,it-IT,ja-JP,hi-IN,ko-KR,nb-NO,nl-NL,pl-PL,pt-BR,pt-PT,ro-RO,ru-RU,sv-SE,tr-TR}] [--region REGION] [--play-command PLAY_COMMAND] [--host HOST] [--port PORT]
                                [--username USERNAME] [--password PASSWORD] [--tls] [--tls-ca-certs TLS_CA_CERTS] [--tls-certfile TLS_CERTFILE] [--tls-keyfile TLS_KEYFILE] [--tls-cert-reqs {CERT_REQUIRED,CERT_OPTIONAL,CERT_NONE}] [--tls-version TLS_VERSION] [--tls-ciphers TLS_CIPHERS] [--site-id SITE_ID]
                                [--debug] [--log-format LOG_FORMAT]

optional arguments:
  -h, --help            show this help message and exit
  --credentials CREDENTIALS
                        Path to AWS credentials file
  --cache-dir CACHE_DIR
                        Directory to cache WAV files
  --voice VOICE         Chosen voice (default: Joanna)
  --engine {standard,neural}
                        Chosen engine (default: neural)
  --output-format {json,mp3,ogg_vorbis,pcm}
                        Chosen engine (default: pcm)
  --sample-rate SAMPLE_RATE
                        Chosen sample rate of the outpt wave sample (default: 22050)
  --language-code {arb,cmn-CN,cy-GB,da-DK,de-DE,en-AU,en-GB,en-GB-WLS,en-IN,en-US,es-ES,es-MX,es-US,fr-CA,fr-FR,is-IS,it-IT,ja-JP,hi-IN,ko-KR,nb-NO,nl-NL,pl-PL,pt-BR,pt-PT,ro-RO,ru-RU,sv-SE,tr-TR}
                        Chosen language (default: en-US)
  --region REGION       Chosen language (default: us-east-1)
  --play-command PLAY_COMMAND
                        Command to play WAV data from stdin (default: publish playBytes)
  --host HOST           MQTT host (default: localhost)
  --port PORT           MQTT port (default: 1883)
  --username USERNAME   MQTT username
  --password PASSWORD   MQTT password
  --tls                 Enable MQTT TLS
  --tls-ca-certs TLS_CA_CERTS
                        MQTT TLS Certificate Authority certificate files
  --tls-certfile TLS_CERTFILE
                        MQTT TLS client certificate file (PEM)
  --tls-keyfile TLS_KEYFILE
                        MQTT TLS client key file (PEM)
  --tls-cert-reqs {CERT_REQUIRED,CERT_OPTIONAL,CERT_NONE}
                        MQTT TLS certificate requirements for broker (default: CERT_REQUIRED)
  --tls-version TLS_VERSION
                        MQTT TLS version (default: highest)
  --tls-ciphers TLS_CIPHERS
                        MQTT TLS ciphers to use
  --site-id SITE_ID     Hermes site id(s) to listen for (default: all)
  --debug               Print DEBUG messages to the console
  --log-format LOG_FORMAT
                        Python logger format
```

