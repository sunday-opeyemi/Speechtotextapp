from tkinter import *
import tkinter.ttk as ttk
from tkinter.filedialog import *
import speech_recognition as sr 
import os, threading, sys, time, pygame, wave, pyaudio
from tkinter.messagebox import *
from pydub import AudioSegment
from pydub.silence import split_on_silence

class SpeechToText:
    def __init__(self):
        self.root = Tk()
        self.root.title("Speech Recognition")
        self.fm = Frame(self.root, width=750, height=800)
        self.yscrol = Scrollbar(self.fm, orient='vertical')
        self.comment= Text(self.fm, width=100, height=30, yscrollcommand = self.yscrol.set)
        self.comment.grid(row=0, column=0, sticky='nsew')
        self.yscrol.config(command = self.comment.yview)
        self.yscrol.grid(row=0, column=1, sticky='ns')
        self.fm.pack(fill=BOTH, expand=True)
        self.menubar()
        self.status = True
        self.root.mainloop()

    def menubar(self):
        self.menu = Frame(self.root, height=300, bg="brown")
        self.menu.pack(side = "top", expand = YES, fill = BOTH)
        self.loadAudio = Button(self.menu, width = 20, text = "Audio to text", foreground="white", bg="black", command =self.audioToTextThread)
        self.loadAudio.pack(side="left", padx=10)
        self.loadMic = Button(self.menu, width = 20, text = "Speech to text", foreground="white", bg="black", command =self.micToTextThread)
        self.progressbar = ttk.Progressbar(self.menu, orient=HORIZONTAL, mode="indeterminate", maximum=100)
        self.info = Label(self.menu, text="", bg="brown", foreground="white")
        self.loadMic.pack(side="left", padx=10)

    def audioToTextThread(self):
        self.playAudio = threading.Thread(target=self.openAudiFfile, name='fromAudio', daemon=True)
        self.playAudio.start()
    
    def micToTextThread(self):
        self.playMic = threading.Thread(target=self.openMicRecord, name='fromMic', daemon=True)
        self.playMic.start()
    
    def playSpeechThread(self):
        self.playspeech = threading.Thread(target=self.playSpeechRecord, name='playSpeech', daemon=True)
        self.playspeech.start()
    
    def transcribSpeechThread(self):
        self.transcribSpeech = threading.Thread(target=self.transcribFromMic, name='transcribSpeech', daemon=True)
        self.transcribSpeech.start()

    def playSpeechRecord(self):
        pygame.init()
        pygame.mixer.init()
        try:
            my_sound = pygame.mixer.Sound(self.in_path)
            my_sound.play()

            while pygame.mixer.get_busy():
                pygame.time.delay(10)
                pygame.event.poll()
        except:
            self.info.destroy()
            self.info = Label(self.menu, text="Unable to play audio file", bg="brown", foreground="white")
            self.info.pack(side="left")

    def stopRecord(self):
        self.status = False

    def openMicRecord(self):
        self.loadMic.configure(text = "Stop recording", command =self.stopRecord)
        self.loadAudio.configure(state=DISABLED, bg='black')
        self.comment.delete(1.0, END)
        filename = "recorded.wav"
        chunk = 1024
        FORMAT = pyaudio.paInt16
        channels = 1
        sample_rate = 44100
        record_seconds = 5
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=channels, rate=sample_rate, input=True, output=True, frames_per_buffer=chunk)
        self.frames = []
        self.transcribSpeechThread()
        while self.status:
            self.info.destroy()
            self.info = Label(self.menu, text="Start recording your speech...", bg="brown", foreground="white")
            self.info.pack(side="left") 
            for i in range(int(sample_rate / chunk * record_seconds)):
                data = stream.read(chunk)
                self.frames.append(data)
                wf = wave.open(filename, "wb")
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(sample_rate)
                wf.writeframes(b"".join(self.frames))
                wf.close()
            self.frames.clear()
        else:
            stream.stop_stream()
            stream.close()
            p.terminate()
            self.info.destroy()
            self.status = True
            self.info = Label(self.menu, text="Recording stopped", bg="brown", foreground="white")
            self.info.pack(side="left")
            self.loadMic.configure(text = "Speech to text", command =self.micToTextThread)
            self.loadAudio.configure(state=NORMAL, bg='black')
        return

    def transcribFromMic(self):
        time.sleep(4)
        while self.status:
            try:
                filename = 'recorded.wav'
                r = sr.Recognizer()
                with sr.AudioFile(filename) as source:
                    audio_data = r.record(source)
                    text = r.recognize_google(audio_data)
            except ValueError:
                self.info.destroy()
                self.info = Label(self.menu, text="Could not recognized your voice try to speek again", bg="brown", foreground="white")
                self.info.pack(side="left")
                time.sleep(2)
            except:
                self.info.destroy()
                self.info = Label(self.menu, text="Having issue conneting. Please check your connection", bg="brown", foreground="white")
                self.info.pack(side="left")
                time.sleep(2)
            else:
                self.info.destroy()
                text = f"{text.capitalize()}. "
                self.comment.insert(END, text +"\n")
                self.comment.see(END)

        return

    def openAudiFfile(self):
        self.loadAudio.configure(text = "Stop recording", command =self.stopRecord)
        self.loadMic.configure(state=DISABLED, bg='black')
        
        try:
            self.in_path = askopenfilename(defaultextension=".txt",
                                       filetypes=[("MP3", "*.mp3"), ("WAV", "*.wav")])
        except:
            pass
        
        if os.path.basename(self.in_path).endswith(".wav"):
            self.info.destroy()
            self.info = Label(self.menu, text="Processing audio... this may take a while", bg="brown", foreground="white")
            self.info.pack(side="left")
            sound = AudioSegment.from_wav(self.in_path)
            chunks = split_on_silence(sound, min_silence_len = 500, silence_thresh = sound.dBFS-14, keep_silence=500,)

        elif os.path.basename(self.in_path).endswith(".mp3"):
            self.info.destroy()
            self.info = Label(self.menu, text="Converting your mp3 file to wav... this may take a while", bg="brown", foreground="white")
            self.info.pack(side="left")
            sound = AudioSegment.from_mp3(self.in_path)
            sound.export("conveted.wav", format="wav")
            time.sleep(2)
            self.info.destroy()
            self.info = Label(self.menu, text="Converting completed", bg="brown", foreground="white")
            self.info.pack(side="left")
            time.sleep(2)
            sound = AudioSegment.from_wav("conveted.wav")
            self.info.destroy()
            self.info = Label(self.menu, text="Processing audio... this may take a while", bg="brown", foreground="white")
            self.info.pack(side="left")
            chunks = split_on_silence(sound, min_silence_len = 500, silence_thresh = sound.dBFS-14, keep_silence=500,)
            # add the sound back to in_path so player can play the voice
            self.in_path = sound
            self.info.destroy()
        else:
            self.info.destroy()
            showinfo("Warning!!", "You need to select a file to continue!!!")
            self.loadMic.configure(state=NORMAL, bg='black')
            self.loadAudio.configure(state=NORMAL, bg='black')
            return
        
        self.pb_start(10)     
        self.comment.delete(1.0, END)
        self.playSpeechThread()

        if not os.path.isdir("audio-chunks"):
            os.mkdir("audio-chunks")
        r = sr.Recognizer()
        for i, audio_chunk in enumerate(chunks, start=1):
            chunk_filename = os.path.join("audio-chunks", f"chunk{i}.wav")
            audio_chunk.export(chunk_filename, format="wav")

            with sr.AudioFile(chunk_filename) as source:
                if self.status == False:
                    self.info.destroy()
                    self.pb_stop()
                    pygame.quit()
                    self.loadAudio.configure(text = "Audio to text", command =self.audioToTextThread)
                    self.loadMic.configure(state=NORMAL, bg='black')
                    self.status = True
                    return

                self.info.destroy()    
                audio_listened = r.record(source)
                try:
                    text = r.recognize_google(audio_listened)
                except ValueError:
                    self.info.destroy()
                    self.info = Label(self.menu, text="Could not recognized the speaker's voice", bg="brown", foreground="white")
                    self.info.pack(side="left")
                    time.sleep(2)
                except:
                    self.info.destroy()
                    self.info = Label(self.menu, text="Having issue conneting. Please check your internet connection", bg="brown", foreground="white")
                    self.info.pack(side="left")
                    time.sleep(2)
                else:
                    text = f"{text.capitalize()}. "
                    self.comment.insert(END, text +"\n")
                    self.comment.see(END)
                finally:
                    self.info.destroy()

        self.pb_stop()
        self.info = Label(self.menu, text="Done Transcribing speech to text", bg="brown", foreground="white")
        self.info.pack(side="left")
        self.loadMic.configure(state=NORMAL, bg='black')
        self.loadAudio.configure(text = "Audio to text", command =self.audioToTextThread)
        return

    def pb_start(self, val):
        """ starts the progress bar """
        self.progressbar = ttk.Progressbar(self.menu, orient=HORIZONTAL, mode="indeterminate", maximum=100)
        self.progressbar.pack(side="left")
        self.progressbar.start(val)

    def pb_stop(self):
        """ stops the progress bar """
        self.progressbar.stop()
        self.progressbar.destroy()

stt = SpeechToText()
