# app_clean.py
import os
import json
import http.client
from io import BytesIO
import gradio as gr
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

KEY_EL = os.getenv("ELEVENLABS_API_KEY", "")
KEY_LLM = os.getenv("API_KEY_302", "")

client_el = None
if KEY_EL:
    client_el = ElevenLabs(api_key=KEY_EL)

PROMPT_A = """\
You are a speech-language pathology helper. Review the ORIGINAL text and the ASR TRANSCRIPT
(which may include recognition mistakes) and identify words or sequences that commonly provoke
stuttering (e.g., complex consonant clusters, multi-syllabic constructions, challenging onsets).

Provide a brief, well-organized diagnostic summary focusing on potential stutter-triggering elements.

ORIGINAL:
{ot}

TRANSCRIPT:
{tt}

Do not provide advice or revision. Respond only with concise diagnostic notes and easy-to-stutter patterns.
"""

PROMPT_B = """\
You are a speech-language pathology helper. Reformulate the ORIGINAL text to lower the likelihood
of stuttering while keeping the original meaning, style, and intention. Favor simpler vocabulary,
shorter phrases, and smoother beginnings of words.

Reference diagnosis details:
{ns}

ORIGINAL:
{ot}

Your reply must contain only the fully rewritten script, no commentary.
"""

PROMPT_C = """\
Transcribe both the ORIGINAL text and the ASR TRANSCRIPT into IPA, marking syllable boundaries.
Return your output in a compact format with clear section labels, for example:

ORIGINAL_IPA:
<original in IPA with syllable breaks>

TRANSCRIPT_IPA:
<transcript in IPA with syllable breaks>

No added explanation or extra notes.

ORIGINAL:
{ot}

TRANSCRIPT:
{tt}
"""

PROMPT_D = """\
You are a speech-language pathology helper. Using the ORIGINAL script, the ASR TRANSCRIPT,
and the IPA annotations, identify segments that are stutter-prone (e.g., long or complex words,
difficult consonant combinations, problematic sound onsets).

Provide a concise, structured diagnostic overview of likely stuttering hotspots.

ORIGINAL:
{ot}

TRANSCRIPT:
{tt}

IPA_ANNOTATIONS:
{ip}

Do not include suggestions or edits. Only provide principled diagnostic notes.
"""

def fn_transcribe(pth: str | None) -> str:
    if not pth:
        return "No audio provided. Please upload or record audio."
    if not KEY_EL:
        return "ELEVENLABS_API_KEY not set. Please configure your environment."
    try:
        with open(pth, "rb") as f:
            buf = BytesIO(f.read())
    except Exception as e:
        return f"Failed to read audio: {e}"
    try:
        tr = client_el.speech_to_text.convert(
            file=buf,
            model_id="scribe_v1",
            tag_audio_events=True,
            language_code="eng",
            diarize=True,
        )
        return tr.text or ""
    except Exception as e:
        return f"Transcription error: {e}"

def fn_llm(model: str, prm: str) -> str:
    if not KEY_LLM:
        return "API_KEY_302 not set. Please configure your environment."
    try:
        con = http.client.HTTPSConnection("api.302.ai")
        pl = json.dumps({
            "model": model,
            "messages": [
                {"role": "user", "content": prm}
            ]
        })
        hd = {
            "Accept": "application/json",
            "Authorization": f"Bearer {KEY_LLM}",
            "Content-Type": "application/json"
        }
        con.request("POST", "/v1/chat/completions", pl, hd)
        rs = con.getresponse()
        raw = rs.read().decode("utf-8")
        con.close()
        out = json.loads(raw)
        msg = out.get("choices", [{}])[0].get("message", {})
        tx = msg.get("content") or msg.get("text") or str(msg)
        return tx.strip()
    except Exception as e:
        return f"LLM API error: {e}"

def cb_transcribe(p):
    return gr.update(value=fn_transcribe(p))

def cb_basic(m, o, t):
    prm = PROMPT_A.format(ot=o or "", tt=t or "")
    rz = fn_llm(m, prm)
    return gr.update(value=rz)

def cb_ipa(m, o, t):
    p1 = PROMPT_C.format(ot=o or "", tt=t or "")
    ipa = fn_llm(m, p1)
    p2 = PROMPT_D.format(ot=o or "", tt=t or "", ip=ipa or "")
    sm = fn_llm(m, p2)
    return gr.update(value=ipa), gr.update(value=sm)

def cb_rewrite(m, o, u, s):
    prm = PROMPT_B.format(ns=s or "", ot=o or "")
    rw = fn_llm(m, prm)
    return gr.update(value=rw)

def passthru(p):
    return p

with gr.Blocks(title="Stutter Up") as ui:
    with gr.Tabs():
        with gr.Tab("Baseline"):
            with gr.Row():
                a_r1 = gr.Audio(label="Record Audio", sources=["microphone"], type="filepath")
                a_f1 = gr.File(label="Audio Download", interactive=False)
                b_t1 = gr.Button("1) Transcribe")
            with gr.Row():
                t_t1 = gr.Textbox(label="Transcribed Text (ASR)", interactive=False, lines=6)
                t_o1 = gr.Textbox(label="Original Script (input)", lines=6)
                dr1 = gr.Dropdown(choices=["gpt-4o-mini", "gpt-5"], value="gpt-4o-mini", label="LLM Model")
                b_a1 = gr.Button("2) Analyze")
            with gr.Row():
                t_s1 = gr.Textbox(label="LLM Summary: Easy-to-Stutter Words", lines=8)
                t_r1 = gr.Textbox(label="Revised Script", lines=8)
                b_r1 = gr.Button("3) Revise Script")
            with gr.Row():
                a_r2 = gr.Audio(label="Post-hoc Record Audio", sources=["microphone"], type="filepath")
                a_f2 = gr.File(label="Post-hoc Audio Download", interactive=False)

            a_r1.change(fn=passthru, inputs=a_r1, outputs=a_f1)
            b_t1.click(fn=cb_transcribe, inputs=[a_r1], outputs=[t_t1])
            b_a1.click(fn=cb_basic, inputs=[dr1, t_o1, t_t1], outputs=[t_s1])
            b_r1.click(fn=cb_rewrite, inputs=[dr1, t_o1, t_t1, t_s1], outputs=[t_r1])
            a_r2.change(fn=passthru, inputs=a_r2, outputs=a_f2)

        with gr.Tab("Baseline+IPA"):
            with gr.Row():
                a_r3 = gr.Audio(label="Record Audio", sources=["microphone"], type="filepath")
                a_f3 = gr.File(label="Audio Download", interactive=False)
                b_t2 = gr.Button("1) Transcribe")
            with gr.Row():
                t_t2 = gr.Textbox(label="Transcribed Text (ASR)", interactive=False, lines=6)
                t_o2 = gr.Textbox(label="Original Script (input)", lines=6)
                t_i2 = gr.Textbox(label="IPA Annotations (LLM Output)", interactive=False, lines=6)
                dr2 = gr.Dropdown(choices=["gpt-4o-mini", "gpt-5"], value="gpt-4o-mini", label="LLM Model")
                b_a2 = gr.Button("2) Analyze (IPA → Diagnosis)")
            with gr.Row():
                t_s2 = gr.Textbox(label="LLM Summary: Easy-to-Stutter Words (IPA-aware)", lines=8)
                t_r2 = gr.Textbox(label="Revised Script", lines=8)
                b_r2 = gr.Button("3) Revise Script")
            with gr.Row():
                a_r4 = gr.Audio(label="Post-hoc Record Audio", sources=["microphone"], type="filepath")
                a_f4 = gr.File(label="Post-hoc Audio Download", interactive=False)

            a_r3.change(fn=passthru, inputs=a_r3, outputs=a_f3)
            b_t2.click(fn=cb_transcribe, inputs=[a_r3], outputs=[t_t2])
            def pipe(m, o, t):
                x, y = cb_ipa(m, o, t)
                return x, y
            b_a2.click(fn=pipe, inputs=[dr2, t_o2, t_t2], outputs=[t_i2, t_s2])
            b_r2.click(fn=cb_rewrite, inputs=[dr2, t_o2, t_t2, t_s2], outputs=[t_r2])
            a_r4.change(fn=passthru, inputs=a_r4, outputs=a_f4)

if __name__ == "__main__":
    ui.launch(share=False)
