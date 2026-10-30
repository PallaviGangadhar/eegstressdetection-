import sys, struct, numpy as np, pyxdf

def varlen(n):
    if n < 256:        return b'\x01' + struct.pack('<B', n)
    if n < 2**32:      return b'\x04' + struct.pack('<I', n)
    return b'\x08' + struct.pack('<Q', n)

def chunk(tag, content):
    return varlen(len(content) + 2) + struct.pack('<H', tag) + content

def header_xml(name, typ, nch, srate, fmt, src):
    return (f'<?xml version="1.0"?><info><name>{name}</name><type>{typ}</type>'
            f'<channel_count>{nch}</channel_count><nominal_srate>{srate}</nominal_srate>'
            f'<channel_format>{fmt}</channel_format><source_id>{src}</source_id>'
            f'<version>1.1</version></info>').encode()

out, files = sys.argv[1], sys.argv[2:]
eeg_t, eeg_x, mk_t, mk_x = [], [], [], []
offset, info = 0.0, None
for f in files:
    streams, _ = pyxdf.load_xdf(f)
    eeg = next((s for s in streams if s['info']['type'][0] == 'EEG' and len(s['time_stamps'])), None)
    if eeg is None:
        print('SKIPPING (no EEG samples):', f); continue
    mks = next((s for s in streams if s['info']['type'][0] == 'Markers' and len(s['time_stamps'])), None)
    info = info or eeg['info']
    t0 = eeg['time_stamps'][0]
    t = eeg['time_stamps'] - t0 + offset
    eeg_t.append(t); eeg_x.append(np.asarray(eeg['time_series'], dtype='<f4'))
    if mks is not None:
        mk_t.append(mks['time_stamps'] - t0 + offset); mk_x += [m[0] for m in mks['time_series']]
    offset = t[-1] + 1/250
n = min(x.shape[1] for x in eeg_x)
print('channels per file:', [x.shape[1] for x in eeg_x], '-> keeping first', n)
eeg_x = [x[:, :n] for x in eeg_x]
eeg_t, eeg_x, mk_t = np.concatenate(eeg_t), np.vstack(eeg_x), np.concatenate(mk_t)
nch = eeg_x.shape[1]

with open(out, 'wb') as fh:
    fh.write(b'XDF:')
    fh.write(chunk(1, b'<?xml version="1.0"?><info><version>1.0</version></info>'))
    fh.write(chunk(2, struct.pack('<I', 1) + header_xml(info['name'][0], 'EEG', nch, 250, 'float32', info['source_id'][0])))
    B = 5000
    for a in range(0, len(eeg_t), B):
        body = struct.pack('<I', 1) + varlen(min(B, len(eeg_t) - a))
        for t, row in zip(eeg_t[a:a+B], eeg_x[a:a+B]):
            body += b'\x08' + struct.pack('<d', t) + row.tobytes()
        fh.write(chunk(3, body))
    fh.write(chunk(2, struct.pack('<I', 2) + header_xml('StressMarkers', 'Markers', 1, 0, 'string', 'stress_exp_v3')))
    body = struct.pack('<I', 2) + varlen(len(mk_t))
    for t, m in zip(mk_t, mk_x):
        mb = str(m).encode()
        body += b'\x08' + struct.pack('<d', t) + varlen(len(mb)) + mb
    fh.write(chunk(3, body))
    for sid, ts, n in ((1, eeg_t, len(eeg_t)), (2, mk_t, len(mk_t))):
        xml = (f'<?xml version="1.0"?><info><first_timestamp>{ts[0]}</first_timestamp>'
               f'<last_timestamp>{ts[-1]}</last_timestamp><sample_count>{n}</sample_count></info>').encode()
        fh.write(chunk(6, struct.pack('<I', sid) + xml))
print('wrote', out)
