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

def recorder():
    contents = audio_recorder(
        energy_threshold = (1000000000,0.0000000002), 
        pause_threshold=0.1, 
        sample_rate = 48_000,
        text="Clickして録音開始　→　"
    )

    return contents

def countdown():
    ph = st.empty()
    N = 60*5
    exit = st.button("Skipして回答")

    for secs in range(N,0,-1):
        mm, ss = secs//60, secs%60
        ph.metric("検討時間", f"{mm:02d}:{ss:02d}")

        time.sleep(1)
        
        if secs == 0:
            return 2

        if exit:
            return 2

def countdown_answer():
    ph = st.empty()
    N = 60*5

    for secs in range(N,0,-1):
        mm, ss = secs//60, secs%60
        ph.metric("回答時間", f"{mm:02d}:{ss:02d}")

        time.sleep(1)
        if secs == 1:
            text_timeout = "時間切れです。リロードして再挑戦してください"
            return text_timeout


st.title('ケース面接Quest')
st.write("ケース面接の練習ができるアプリです。")
st.text("① 設問番号を選ぶと設問文が表示されます  \n② 5分間の検討時間の後、回答（音声録音）に移行します  \n③ 回答（音声）は文字起こしされます。誤字を修正して提出してください  \n④ 数日後、現役コンサルタントのFeedbackをメールに送付します！！")

if "state" not in st.session_state:
   st.session_state["state"] = 0

if st.button("さっそくTry!"):
    st.session_state["state"] = 1

if st.session_state["state"] == 0:
    st.stop()

st.info('問題番号を選ぶと回答が始まります')
df_list = pd.read_csv("question_list.csv", header = None)
option = st.selectbox(
    '問題番号を選択してください',
    df_list[0])
question = ""
if option is not df_list[0][0]:
    question = df_list[df_list[0]==option].iloc[0,1]

if question == "":
    st.stop()

st.success('■ 設問：　' + question)

if st.session_state["state"] == 1:
    st.session_state["state"] = countdown()

contents = recorder()

if contents == None:
    st.info('①　アイコンボタンを押して回答録音　(アイコンが赤色で録音中)。  \n②　もう一度押して回答終了　(再度アイコンが黒色になれば完了)')
    contents = countdown_answer()
    st.info(contents)
    st.stop()

st.info('【録音完了！　音声分析中...】  \n　↓分析中は録音データをチェック！')
st.audio(contents)

bucket_name = 'tech0-speachtotext'
destination_blob_name = 'streamlit-mono1.wav'

upload_blob_from_memory(bucket_name, contents, destination_blob_name)
transcript = transcript(bucket_name)
text = '。\n'.join(transcript)

status = st.info('分析が完了しました！')

with st.form("form1"):
    name = st.text_input("名前/Name")
    email = st.text_input("メールアドレス/Mail address")
    massage = st.text_area("回答内容（修正可能）",text)

    submit = st.form_submit_button("Submit")

if submit:
    st.info('回答が提出されました。後ほどご入力頂いたメール宛にFeedbackを送付します')

st.stop()














