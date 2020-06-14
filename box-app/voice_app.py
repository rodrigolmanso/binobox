# -*- Coding: UTF-8 -*-
#coding: utf-8
#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer
import os
import time

if not os.path.exists("model"):
    print ("Please download the model from https://github.com/alphacep/vosk-api/blob/master/doc/models.md and unpack as 'model' in the current folder.")
    exit (1)

import pika
import threading

def callback(ch, method, properties, body):
    print("Received updated event %r" % body)
    if body == b'postos_combustiveis':
        say("Olá Dejair, recebemos uma atualização dos postos de combustíveis")

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='events_from_boxapp')
channel.queue_declare(queue='updated')
channel.basic_consume(queue='updated', auto_ack=True, on_message_callback=callback)
mq_recieve_thread = threading.Thread(target=channel.start_consuming)

import pyttsx3
import pyaudio
model = Model("model")
rec = KaldiRecognizer(model, 16000)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)

def start():
    import json
    from joblib import load, dump
    import numpy as np
    import pandas as pd

    stream.start_stream()

    mq_recieve_thread.start()

    while True:
        data = stream.read(4000, exception_on_overflow = False)
        if len(data) == 0:
            break

        if rec.AcceptWaveform(data):
            text = json.loads(rec.Result())["text"]

            if "box" in text:
                send("Dejair: " + text)
                reply = "Bom Dia Dejair"
                send("BinoBox: " + reply)
                say(reply)

            if "posto" in text and "perto" in text:
                send("Dejair: " + text)
                reply = "Tem um posto de combustível em 3 quilômetros"
                send("BinoBox: " + reply)
                say(reply)

def main():
    start()

def say(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.stop()

def send(text):
    print(text)
    channel.basic_publish(exchange='', routing_key='events_from_boxapp', body=text)

if __name__ == "__main__":
    try:
        main()
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

        channel.stop_consuming()
        connection.close()
        mq_recieve_thread._Thread__stop()