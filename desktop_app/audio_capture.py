import io
import time
import wave

import array

try:
    import pyaudiowpatch as pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False


def record_system_audio_wav(duration_sec=5.5):
    """
    Записывает системный звук из наушников/колонок (WASAPI Loopback).
    Если Loopback недоступен или в наушниках полная тишина, пробует записать с микрофона.
    Возвращает кортеж: (wav_bytes, source_name) или (None, error_message).
    """
    if not HAS_PYAUDIO:
        return None, "Модуль захвата звука не установлен"

    p = pyaudio.PyAudio()
    try:
        target_device = None
        source_label = "Системный звук"

        # 1. Ищем активное устройство вывода WASAPI Loopback (наушники / колонки)
        try:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_out_idx = wasapi_info.get("defaultOutputDevice", -1)
            if default_out_idx >= 0:
                default_speakers = p.get_device_info_by_index(default_out_idx)
                if not default_speakers.get("isLoopbackDevice", False):
                    for loopback in p.get_loopback_device_info_generator():
                        if default_speakers["name"] in loopback["name"]:
                            target_device = loopback
                            break
                    if target_device is None:
                        for loopback in p.get_loopback_device_info_generator():
                            target_device = loopback
                            break
                else:
                    target_device = default_speakers
                if target_device:
                    source_label = "Звук из наушников/ПК"
        except Exception:
            target_device = None

        # 2. Если Loopback не найден, берем стандартный микрофон
        if target_device is None:
            try:
                default_in = p.get_default_input_device_info()
                target_device = default_in
                source_label = "Микрофон"
            except Exception:
                return None, "Не найдено ни устройство вывода звука, ни микрофон"

        channels = max(1, min(int(target_device.get("maxInputChannels", 2)), 2))
        rate = int(target_device.get("defaultSampleRate", 44100))
        frames = []

        def callback(in_data, frame_count, time_info, status):
            frames.append(in_data)
            return (in_data, pyaudio.paContinue)

        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=rate,
            frames_per_buffer=1024,
            input=True,
            input_device_index=target_device["index"],
            stream_callback=callback
        )

        stream.start_stream()
        time.sleep(duration_sec)
        stream.stop_stream()
        stream.close()

        raw_pcm = b"".join(frames)

        # Если в Loopback была полная тишина (0 пакетов), пробуем записать 4 сек с микрофона
        if len(raw_pcm) < 1000:
            try:
                default_in = p.get_default_input_device_info()
                if default_in["index"] != target_device["index"]:
                    mic_frames = []
                    mic_channels = max(1, min(int(default_in.get("maxInputChannels", 1)), 2))
                    mic_rate = int(default_in.get("defaultSampleRate", 44100))

                    def mic_cb(in_data, frame_count, time_info, status):
                        mic_frames.append(in_data)
                        return (in_data, pyaudio.paContinue)

                    mic_stream = p.open(
                        format=pyaudio.paInt16,
                        channels=mic_channels,
                        rate=mic_rate,
                        frames_per_buffer=1024,
                        input=True,
                        input_device_index=default_in["index"],
                        stream_callback=mic_cb
                    )
                    mic_stream.start_stream()
                    time.sleep(4.0)
                    mic_stream.stop_stream()
                    mic_stream.close()
                    raw_pcm = b"".join(mic_frames)
                    channels = mic_channels
                    rate = mic_rate
                    source_label = "Микрофон"
            except Exception:
                pass

        if len(raw_pcm) < 500:
            return None, "В наушниках/колонках сейчас тишина (включите видео или звук звонка)"

        # Сжимаем стерео 48кГц -> моно 16кГц для быстрой передачи в ИИ
        try:
            samples = array.array('h', raw_pcm)
            if channels == 2 and len(samples) >= 2:
                samples = array.array('h', ((samples[i] + samples[i + 1]) // 2 for i in range(0, len(samples) - 1, 2)))
                channels = 1
            if rate >= 32000:
                step = max(1, rate // 16000)
                samples = samples[::step]
                rate = rate // step
            raw_pcm = samples.tobytes()
        except Exception:
            pass

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(rate)
            wf.writeframes(raw_pcm)

        return wav_buffer.getvalue(), source_label

    except Exception as e:
        return None, f"Ошибка записи звука: {str(e)[:50]}"
    finally:
        try:
            p.terminate()
        except Exception:
            pass
