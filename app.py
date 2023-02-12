from google.cloud import storage
import os
import io
import numpy as np
import pandas as pd
import audioop
import time
from google.cloud import speech


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'tech0-step3-te-bd23bed77076.json'


import streamlit as st
from audio_recorder_streamlit import audio_recorder

def upload_blob_from_memory(bucket_name, contents, destination_blob_name):
    """Uploads a file to the bucket."""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    contents = audioop.tomono(contents, 1, 0, 1)
    blob.upload_from_string(contents)


    print(
        f"{destination_blob_name} with contents {contents} uploaded to {bucket_name}."
    )
    return contents

def gcs_url(bucket_name): 
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs()
    id_list = []
    for blob in blobs:
        id_list.append(blob.id)
    url_id = id_list[0].split('.wav')[0]
    gcs_uri="gs://"+url_id+".wav"
    return gcs_uri


def transcript(bucket_name):
    gcs_uri = gcs_url(bucket_name)
    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=48000,
        language_code="ja-JP",
    )

    operation = speech.SpeechClient().long_running_recognize(config=config, audio=audio)
    response = operation.result(timeout=90)

    transcript = []
    for result in response.results:
        transcript.append(result.alternatives[0].transcript)
        
    return transcript


st.title('フェルミ推定/ケース面接アプリ')
st.markdown('問題')

df_list = pd.read_csv("question_list.csv", header = None, encoding="shift-jis" )
option = st.selectbox(
    '問題番号を選択してください',
    df_list[0])
question = ""
question = df_list[df_list[0]==option].iloc[0,1]

if st.button('出題'):
    st.session_state["button1"] = 1

if st.session_state["button1"] is not 1:
    st.warning('出題ボタンを押すと回答が始まります')
    st.stop()

st.warning('質問：　' + question)

contents = audio_recorder(
    energy_threshold = (1000000000,0.0000000002), 
    pause_threshold=0.1, 
    sample_rate = 48_000,
    text="アイコンをClickして面接開始　→　",
    icon_name="user",
    )

st.write('※ 発言終了後はもう一度Click')
st.audio(contents)

bucket_name = 'tech0-speachtotext'
destination_blob_name = 'streamlit-mono1.wav'

upload_blob_from_memory(bucket_name, contents, destination_blob_name)
st.write('分析中です...')
transcript = transcript(bucket_name)
text = '。\n'.join(transcript)

status = st.write('分析が完了しました！')

txt = st.text_area("修正が完了したら、【Submit】ボタンを押して提出してください",text, height = 300)
st.button('Submit!')

st.stop()













