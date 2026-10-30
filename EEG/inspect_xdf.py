import pyxdf
import glob
import numpy as np

files = sorted(glob.glob("Data/raw/**/*.xdf", recursive=True))

if not files:
    print("No XDF files found.")
    raise SystemExit(1)

path = files[0]
print("Inspecting:", path)

streams, header = pyxdf.load_xdf(path)

for i, s in enumerate(streams):
    info = s["info"]
    name = info.get("name", ["unknown"])[0]
    typ = info.get("type", ["unknown"])[0]
    rate = info.get("nominal_srate", ["unknown"])[0]
    data = np.asarray(s.get("time_series", []))

    print(f"\nStream {i}")
    print("Name:", name)
    print("Type:", typ)
    print("Nominal sampling rate:", rate)
    print("Data shape:", data.shape)
    print("Data dtype:", data.dtype)

    if "marker" in str(name).lower() or "marker" in str(typ).lower():
        print("First marker samples:", data[:15].tolist())
