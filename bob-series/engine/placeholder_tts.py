import json,sys,wave,subprocess,os
from piper import PiperVoice
from piper.config import SynthesisConfig
W=sys.argv[1]; S=json.load(open(sys.argv[2]))
v=PiperVoice.load(f'{W}/voices/en_US-ryan-high.onnx')
cfg=SynthesisConfig(length_scale=1.02)
for c in S['chunks']:
    out=f"{W}/vo_placeholder/{c['id']}.wav"
    with wave.open(out,'wb') as w: v.synthesize_wav(c['text'].replace('\n',' '),w,syn_config=cfg)
    d=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',out]))
    print(c['id'],round(d,2))
