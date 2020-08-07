"""Hermes MQTT service for Rhasspy TTS with Amazon Polly."""
import argparse
import asyncio
import logging
from pathlib import Path

import paho.mqtt.client as mqtt
import rhasspyhermes.cli as hermes_cli

from . import TtsHermesMqtt

_LOGGER = logging.getLogger('rhasspytts_polly_hermes')

VALID_ENGINES = ['standard', 'neural']
VALID_OUTPUT_FORMATS = ['json', 'mp3', 'ogg_vorbis', 'pcm']
VALID_LANGUAGE_CODES = [
    'arb', 'cmn-CN', 'cy-GB', 'da-DK', 'de-DE', 'en-AU', 'en-GB', 'en-GB-WLS',
    'en-IN', 'en-US', 'es-ES', 'es-MX', 'es-US', 'fr-CA', 'fr-FR', 'is-IS',
    'it-IT', 'ja-JP', 'hi-IN', 'ko-KR', 'nb-NO', 'nl-NL', 'pl-PL', 'pt-BR',
    'pt-PT', 'ro-RO', 'ru-RU', 'sv-SE', 'tr-TR'
]


# -----------------------------------------------------------------------------

def main():
    """Main method."""
    parser = argparse.ArgumentParser(prog='rhasspy-tts-polly-hermes')
    parser.add_argument(
        '--credentials',
        required=True,
        help='Path to AWS credentials file',
    )
    parser.add_argument(
        '--cache-dir', required=True, help='Directory to cache WAV files'
    )
    parser.add_argument(
        '--voice', default='Joanna', help='Chosen voice (default: Joanna)'
    )
    parser.add_argument(
        '--engine',
        choices=VALID_ENGINES,
        default='neural',
        help='Chosen engine (default: neural)'
    )
    parser.add_argument(
        '--sample-rate',
        default=16000,
        type=int,
        help='Chosen sample rate of the outpt wave sample (default: 16000)',
    )
    parser.add_argument(
        '--language-code',
        choices=VALID_LANGUAGE_CODES,
        default='en-US',
        help='Chosen language (default: en-US)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='Chosen language (default: us-east-1)'
    )
    parser.add_argument(
        '--play-command',
        help='Command to play WAV data from stdin (default: publish playBytes)',
    )
    hermes_cli.add_hermes_args(parser)
    args = parser.parse_args()

    hermes_cli.setup_logging(args)
    _LOGGER.debug(args)

    args.credentials = Path(args.credentials)
    args.cache_dir = Path(args.cache_dir)

    # Listen for messages
    client = mqtt.Client()
    hermes = TtsHermesMqtt(
        client,
        credentials=args.credentials,
        cache_dir=args.cache_dir,
        voice=args.voice,
        engine=args.engine,
        sample_rate=args.sample_rate,
        language_code=args.language_code,
        region=args.region,
        play_command=args.play_command,
        site_ids=args.site_id,
    )

    _LOGGER.debug('Connecting to %s:%s', args.host, args.port)
    hermes_cli.connect(client, args)
    client.loop_start()

    try:
        # Run event loop
        asyncio.run(hermes.handle_messages_async())
    except KeyboardInterrupt:
        pass
    finally:
        _LOGGER.debug('Shutting down')
        client.loop_stop()


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
