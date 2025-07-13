import whisper
import sounddevice as sd
import numpy as np
import tempfile
import scipy.io.wavfile

# Whisper 모델 불러오기 (base, small, medium, large 선택 가능)
model = whisper.load_model("base")  # 또는 "small", "medium", "large"

# 마이크 설정
samplerate = 16000  # Whisper 권장 샘플레이트
duration = 5  # 녹음 시간 (초)

def record_audio():
    print("🎤 녹음 시작...")
    recording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    print("✅ 녹음 완료!")
    return recording

def save_wav(audio_data, samplerate):
    # 임시 wav 파일로 저장
    tmpfile = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    scipy.io.wavfile.write(tmpfile.name, samplerate, audio_data)
    return tmpfile.name

def transcribe_audio(file_path):
    print("📄 Whisper 모델로 텍스트 추출 중...")
    result = model.transcribe(file_path, language="ko")  # 한국어라고 명시
    return result["text"]

def main():
    audio = record_audio()
    file_path = save_wav(audio, samplerate)
    text = transcribe_audio(file_path)
    print("📝 인식된 텍스트:", text)

main()
