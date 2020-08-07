"""Hermes MQTT server for Rhasspy TTS using Amazon Polly"""
import asyncio
import hashlib
import io
import logging
import os
import shlex
import subprocess
import typing
import wave
from pathlib import Path
from uuid import uuid4

import boto3
from rhasspyhermes.audioserver import AudioPlayBytes, AudioPlayError, AudioPlayFinished
from rhasspyhermes.base import Message
from rhasspyhermes.client import GeneratorType, HermesClient, TopicArgs
from rhasspyhermes.tts import GetVoices, TtsError, TtsSay, TtsSayFinished, Voice, Voices

_LOGGER = logging.getLogger('rhasspytts_polly_hermes')

# -----------------------------------------------------------------------------


class TtsHermesMqtt(HermesClient):
    """Hermes MQTT server for Rhasspy TTS using Amazon Polly."""

    def __init__(
        self,
        client,
        credentials: Path,
        cache_dir: Path,
        voice: str = 'Joanna',
        engine: str = 'neural',
        output_format: str = 'pcm',
        sample_rate: int = 22050,
        language_code: str = 'en-US',
        region: str = 'us-east-1',
        play_command: typing.Optional[str] = None,
        site_ids: typing.Optional[typing.List[str]] = None,
    ):
        super().__init__('rhasspytts_polly_hermes', client, site_ids=site_ids)

        self.subscribe(TtsSay, GetVoices, AudioPlayFinished)

        self.credentials = credentials
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = self.credentials

        self.cache_dir = cache_dir
        self.voice = voice
        self.engine = engine
        self.output_format = output_format
        self.sample_rate = int(sample_rate)
        self.language_code = language_code
        
        self.region = region
        os.environ['AWS_REGION'] = self.region

        self.play_command = play_command

        self.play_finished_events: typing.Dict[typing.Optional[str], asyncio.Event] = {}

        # Seconds added to playFinished timeout
        self.finished_timeout_extra: float = 0.25

        # Create cache directory in profile if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.polly_client = boto3.Session().client('polly')

    # -------------------------------------------------------------------------

    async def handle_say(
        self, say: TtsSay
    ) -> typing.AsyncIterable[
        typing.Union[
            TtsSayFinished,
            typing.Tuple[AudioPlayBytes, TopicArgs],
            TtsError,
            AudioPlayError,
        ]
    ]:
        """Run TTS system and publish WAV data."""
        wav_bytes: typing.Optional[bytes] = None

        try:
            # Try to pull WAV from cache first
            sentence_hash = self.get_sentence_hash(say.text)
            cached_wav_path = self.cache_dir / f'{sentence_hash.hexdigest()}.wav'

            if cached_wav_path.is_file():
                # Use WAV file from cache
                _LOGGER.debug('Using WAV from cache: %s', cached_wav_path)
                wav_bytes = cached_wav_path.read_bytes()

            if not wav_bytes:
                # Run text to speech
                assert self.polly_client, 'No Boto3 Client'

                _LOGGER.debug(
                    'Calling AWS (lang=%s, voice=%s, engine=%s, rate=%s)',
                    self.language_code,
                    self.voice,
                    self.engine,
                    self.sample_rate,
                )

                if say.text.startswith('<speak>'):
                    response = self.polly_client.synthesize_speech(
                        Engine=self.engine,
                        LanguageCode=self.language_code,
                        OutputFormat=self.output_format,
                        SampleRate=str(self.sample_rate),
                        Text=say.text,
                        TextType='ssml',
                        VoiceId=self.voice
                    )
                else:
                    response = self.polly_client.synthesize_speech(
                        Engine=self.engine,
                        LanguageCode=self.language_code,
                        OutputFormat=self.output_format,
                        SampleRate=str(self.sample_rate),
                        Text=say.text,
                        TextType='text',
                        VoiceId=self.voice
                    )

                wav_bytes = response['AudioStream'].read()

            assert wav_bytes, 'No WAV data received'
            _LOGGER.debug('Got %s byte(s) of WAV data', len(wav_bytes))

            if wav_bytes:
                finished_event = asyncio.Event()

                # Play WAV
                if self.play_command:
                    try:
                        # Play locally
                        play_command = shlex.split(
                            self.play_command.format(lang=say.lang)
                        )
                        _LOGGER.debug(play_command)

                        subprocess.run(play_command, input=wav_bytes, check=True)

                        # Don't wait for playFinished
                        finished_event.set()
                    except Exception as e:
                        _LOGGER.exception('play_command')
                        yield AudioPlayError(
                            error=str(e),
                            context=say.id,
                            site_id=say.site_id,
                            session_id=say.session_id,
                        )
                else:
                    # Publish playBytes
                    request_id = say.id or str(uuid4())
                    self.play_finished_events[request_id] = finished_event

                    yield (
                        AudioPlayBytes(wav_bytes=wav_bytes),
                        {'site_id': say.site_id, 'request_id': request_id},
                    )

                # Save to cache
                with open(cached_wav_path, 'wb') as cached_wav_file:
                    cached_wav_file.write(wav_bytes)

                try:
                    # Wait for audio to finished playing or timeout
                    wav_duration = TtsHermesMqtt.get_wav_duration(wav_bytes)
                    wav_timeout = wav_duration + self.finished_timeout_extra

                    _LOGGER.debug('Waiting for play finished (timeout=%s)', wav_timeout)
                    await asyncio.wait_for(finished_event.wait(), timeout=wav_timeout)
                except asyncio.TimeoutError:
                    _LOGGER.warning('Did not receive playFinished before timeout')

        except Exception as e:
            _LOGGER.exception('handle_say')
            yield TtsError(
                error=str(e),
                context=say.id,
                site_id=say.site_id,
                session_id=say.session_id,
            )
        finally:
            yield TtsSayFinished(
                id=say.id, site_id=say.site_id, session_id=say.session_id
            )

    # -------------------------------------------------------------------------

    async def handle_get_voices(
        self, get_voices: GetVoices
    ) -> typing.AsyncIterable[Voices]:
        """Publish list of available voices."""
        voices: typing.List[Voice] = []

        try:
            response = self.polly_client.describe_voices(
                Engine=self.engine,
                LanguageCode=self.language_code,
                IncludeAdditionalLanguageCodes=True
            )

            for v in response['Voices']:
                voice = Voice(voice_id=v['Id'])
                voice.description = v['Id']
                voices.append(voice)      
        except Exception as e:
            _LOGGER.exception('handle_get_voices')
            yield TtsError(
                error=str(e), context=get_voices.id, site_id=get_voices.site_id
            )

        # Publish response
        yield Voices(voices=voices, id=get_voices.id, site_id=get_voices.site_id)

    # -------------------------------------------------------------------------

    async def on_message(
        self,
        message: Message,
        site_id: typing.Optional[str] = None,
        session_id: typing.Optional[str] = None,
        topic: typing.Optional[str] = None,
    ) -> GeneratorType:
        """Received message from MQTT broker."""
        if isinstance(message, TtsSay):
            async for say_result in self.handle_say(message):
                yield say_result
        elif isinstance(message, GetVoices):
            async for voice_result in self.handle_get_voices(message):
                yield voice_result
        elif isinstance(message, AudioPlayFinished):
            # Signal audio play finished
            finished_event = self.play_finished_events.pop(message.id, None)
            if finished_event:
                finished_event.set()
        else:
            _LOGGER.warning('Unexpected message: %s', message)

    # -------------------------------------------------------------------------

    def get_sentence_hash(self, sentence: str):
        """Get hash for cache."""
        m = hashlib.md5()
        m.update(
            '_'.join(
                [
                    sentence,
                    self.voice,
                    str(self.sample_rate),
                    self.language_code,
                ]
            ).encode('utf-8')
        )

        return m

    @staticmethod
    def get_wav_duration(wav_bytes: bytes) -> float:
        """Return the real-time duration of a WAV file"""
        with io.BytesIO(wav_bytes) as wav_buffer:
            wav_file: wave.Wave_read = wave.open(wav_buffer, 'rb')
            with wav_file:
                width = wav_file.getsampwidth()
                rate = wav_file.getframerate()

                # getnframes is not reliable.
                # espeak inserts crazy large numbers.
                guess_frames = (len(wav_bytes) - 44) / width

                return guess_frames / float(rate)
