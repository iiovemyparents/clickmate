import subprocess
import speech_recognition as sr
import winreg
import asyncio
import edge_tts
import pyaudio
from transformers import pipeline
from enum import Enum
from typing import NoReturn
from util import test
from pydub import AudioSegment

class CallType(Enum):
    CLICK_BUTTON = 0
    OPEN_WINDOW = 1
    UNKTNOWN_INTENTION = 2

class Clickmate:
    def __init__(self):
        self.is_stopped: bool = False
        self.classifier = pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
        )
        self.noise_duration = 0.15
        self.timeout = 2.5
        self.phrase_timeout = 2.5

        self.programs = self.get_installed_programs()
        self.programs.append(("파일 탐색기", r"C:\Windows\explorer.exe"))
        self.programs.append(("계산기", r"C:\Windows\System32\calc.exe"))
        self.programs.append(("메모장", r"C:\Windows\System32\notepad.exe"))
        self.programs.append(("제어판", r"C:\Windows\System32\control.exe"))
        #self.programs.append(("명령 프롬프트", r"C:\Windows\System32\cmd.exe"))

        test(self.programs)

    def run(self):
        asyncio.run(self.loop())

    async def loop(self) -> NoReturn:
        while not self.is_stopped:
            command_text = await self.wait_mic_to_text() # 블로킹 상태

            if command_text is None:
                continue

            await self.talk("명령을 처리하고 있어요, 잠시만 기다려주세요")
            call_type = self.inference(command_text) # 자연어 추론
            
            if call_type == CallType.CLICK_BUTTON:
                await self.click()
            elif call_type == CallType.OPEN_WINDOW:
                await self.run_program(self.filtering(command_text))
            else:
                await self.unknown_intention()

    def log(self, message: str) -> NoReturn:
        print(f"[LOG] {message}")

    async def talk(self, message):
        self.log(message)

        communicate = edge_tts.Communicate(message, voice="ko-KR-InJoonNeural")
        await communicate.save("output.mp3")

        audio = AudioSegment.from_file("output.mp3", format="mp3")
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(audio.sample_width),
                        channels=audio.channels,
                        rate=audio.frame_rate,
                        output=True)

        stream.write(audio.raw_data)

        stream.stop_stream()
        stream.close()
        p.terminate()

    async def wait_mic_to_text(self) -> str:
        r = sr.Recognizer()
        mic = sr.Microphone(device_index=1)
        
        await self.talk("목소리를 듣고 있어요, 무엇을 하고 싶으신가요?")
        
        with mic as source:
            r.adjust_for_ambient_noise(source, duration=self.noise_duration)

            while True:
                try:
                    audio = r.listen(source, timeout=self.timeout, phrase_time_limit=self.phrase_timeout)
                    self.log("음성을 입력 받았습니다.")
                    break
                except sr.WaitTimeoutError:
                    self.log(f"{self.timeout}초 동안 음성 입력 없어 다시 입력을 대기합니다.")
                except Exception as e:
                    self.log(f"오류가 발생했습니다. 다시 재시도합니다...\n오류 메세지: {e}")
            
        try:
            result = r.recognize_google(audio, language="ko-KR")
            self.log(f"인식된 명령어: {result}")
            return result
        except sr.UnknownValueError:
            await self.talk("알 수 없는 에러가 발생했어요. 다시 한번 더 말씀해주세요.")
        except sr.RequestError:
            await self.talk("Google API 요청에 실패했어요.")
        except sr.WaitTimeoutError:
            await self.talk("음성 대기 시간이 초과되었어요.")
        return None
    
    def inference(self, text: str) -> CallType:
        candidate_labels = ["버튼 클릭", "창 열기"]
        result = self.classifier(text, candidate_labels, hypothesis_template="이 문장은 {}에 대한 요청이다.")
        top_label = result["labels"][0]

        if top_label == "버튼 클릭":
            return CallType.CLICK_BUTTON
        elif top_label == "창 열기":
            return CallType.OPEN_WINDOW
        else:
            return CallType.UNKTNOWN_INTENTION

    def get_installed_programs(self):
        programs = []
        uninstall_keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        for key_path in uninstall_keys:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                display_icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                                programs.append((display_name, display_icon))
                            except FileNotFoundError:
                                pass
            except FileNotFoundError:
                pass
        return programs
    
    def filtering(self, text: str) -> str:
        for prog in self.programs:
            if prog[0] in text:
                return prog[0]
            
        return None
    
    async def run_program(self, name) -> bool:
        if name is None:
            return False

        for display_name, display_icon in self.programs:
            if not isinstance(display_name, str):
                continue

            if name in display_name:
                exe_path = display_icon.split(",")[0]

                try:
                    subprocess.Popen([exe_path])
                    await self.talk(f"성공적으로 {name}을 열었어요")
                    return True
                except Exception as e:
                    print(f"프로그램 실행 오류: {e}")
                    return False

        return False

    # Command Area
    async def click(self):
        print("마우스 클릭")

    async def unknown_intention(self):
        await self.talk("무슨 의미인지 알아듣지 못했어요. 다시 한번 더 말씀해주세요.")