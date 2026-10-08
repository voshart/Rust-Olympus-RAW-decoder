"""One-off preregistered numerical measurement. No complete compressed decoder."""
import hashlib,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT.parent/'olympus-public'
sys.path.insert(0,str(PUBLIC/'tools'))
from inspect_orf import inspect
sources=[
    PUBLIC/'corpus/voshart-olympus/P6190137_EM5MarkII_Lumix G 20mmF1.7 II.ORF',
    PUBLIC/'corpus/voshart-olympus/P5121636EM5MkIII_Olympus M60mm F2.8macro.ORF',
    ROOT/'plan/orf-research/public-2026-10-08/samples/pixls-1993.ORF',
    ROOT/'plan/orf-research/public-2026-10-08/samples/pixls-2978.ORF',
    ROOT/'plan/orf-research/public-2026-10-08/samples/pixls-6946.ORF',
]
observations=[]
for path in sources:
    record=inspect(path)
    encoded=bytes.fromhex(record['strips'][0]['prefix_32_hex'])
    bitstring=''.join(f'{b:08b}' for b in encoded)
    cursor=7*8
    fields=[]
    def field(count):
        global cursor
        at=cursor
        if cursor+count>len(bitstring):raise ValueError('hypothesis exceeded prefix observation')
        cursor+=count
        return int(bitstring[at:cursor],2)
    for word in range(2):
        start=cursor
        flags=field(3)
        zeros=0
        while zeros<12 and bitstring[cursor]=='0':
            cursor+=1;zeros+=1
        if zeros==12:
            upper=field(11)
            ignored=field(1)
        else:
            ignored=field(1)
            upper=zeros
        low=field(4)
        high_part=upper*16+low
        value=((~high_part if flags&4 else high_part)*4+(flags&3))&65535
        fields.append(dict(start_bit=start,end_bit_exclusive=cursor,flags=flags,zero_count=zeros,
                           quotient=upper,terminator_or_extra_bit=ignored,remainder=low,
                           high_part=high_part,candidate_value=value))
    observation=dict(file=path.name,input_sha256=record['sha256'],fields=fields,
                     interpretation='initial-two-values-only',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    observations.append(observation)
    print('CANDIDATE BEFORE REFERENCE',json.dumps(observation),flush=True)

# Acquire independent arrays only after every candidate has been computed.
sys.path.insert(0,str(ROOT/'plan/orf-research/runtime'))
import rawpy
for path,result in zip(sources,observations):
    with rawpy.imread(str(path)) as raw:
        first=raw.raw_image[0,:2].tolist()
        result.update(rawpy=rawpy.__version__,libraw=list(rawpy.libraw_version),reference_first_two_values=first,
                      matches=[f['candidate_value']==v for f,v in zip(result['fields'],first)])
        print('REFERENCE',path.name,first,result['matches'],flush=True)
out=PUBLIC/'research/results/initial-token-hypothesis.json'
with out.open('x',encoding='utf-8') as stream:
    json.dump(dict(schema=1,protocol='research/compressed-next-experiment.md',cases=observations),stream,indent=2)
    stream.write('\n')
