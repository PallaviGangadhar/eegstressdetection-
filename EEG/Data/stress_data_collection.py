#!/usr/bin/env python3

"""
EEG Stress Experiment - Stable Version (No GL Crash)

✔ Fixes OpenGL TextStim crash
✔ Uses safe rendering settings
✔ Accurate timing (PsychoPy clock)
✔ Numeric LSL markers
✔ ESC to quit safely

Trial (120s):
- Baseline: 50s → 100
- Cue: 10s → 110
- Stimulus: 50s → 120
- Video End → 130
- Rest: 10s → 140
"""

import os
import csv
import datetime
import argparse

# 🔧 IMPORTANT: set prefs BEFORE importing visual
from psychopy import prefs
prefs.general['winType'] = 'pyglet'

from pylsl import StreamInfo, StreamOutlet
from psychopy import visual, core, event

# ==========================
# CONFIG
# ==========================

BASELINE_SEC = 10
CUE_SEC = 10
STIMULUS_SEC = 1110
REST_SEC = 40

MARKERS = {
    "trial_start": 90,
    "baseline": 100,
    "cue": 110,
    "stimulus": 120,
    "video_end": 130,
    "rest": 140,
    "stress_peak": 150,
    "non_stress": 160,
    "artifact": 200
}

OUTPUT_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================
# UTIL FUNCTIONS
# ==========================

def send_marker(outlet, code):
    ts = datetime.datetime.utcnow().isoformat()
    outlet.push_sample([str(code)])  # numeric marker
    print(f"{ts} → Marker {code}")
    return ts


def check_exit(keys, win):
    if 'escape' in keys:
        win.close()
        core.quit()


# ==========================
# SAFE TEXT CREATION
# ==========================

def create_safe_text(win):
    try:
        return visual.TextStim(
            win,
            text="",
            color='white',
            height=30,
            font='Arial',
            units='pix'
        )
    except Exception as e:
        print("⚠ TextStim failed, using fallback:", e)
        return None


def draw_text(win, text_obj, message):
    if text_obj:
        text_obj.text = message
        text_obj.draw()
    win.flip()


# ==========================
# MAIN EXPERIMENT
# ==========================

def run_experiment(participant, condition, trials):

    # LSL setup
    info = StreamInfo('StressMarkers', 'Markers', 1, 0, 'string', 'stress_exp_v3')
    outlet = StreamOutlet(info)

    # 🔧 SAFE WINDOW
    win = visual.Window(
        size=(800, 600),
        fullscr=False,
        screen=0,
        winType='pyglet',
        allowGUI=True,
        monitor='testMonitor',
        units='pix',
        color='black'
    )

    text = create_safe_text(win)

    log = []

    # START SCREEN
    draw_text(win, text, f"Participant: {participant}\nCondition: {condition}\n\nSPACE = Start | ESC = Quit")
    keys = event.waitKeys(keyList=['space', 'escape'])
    if 'escape' in keys:
        win.close()
        return

    for trial in range(1, trials + 1):

        # ======================
        # TRIAL START
        # ======================
        ts = send_marker(outlet, MARKERS["trial_start"])
        log.append([ts, trial, "trial_start", 90])

        # ======================
        # BASELINE
        # ======================
        ts = send_marker(outlet, MARKERS["baseline"])
        log.append([ts, trial, "baseline_start", 100])

        clock = core.Clock()
        clock.reset()

        while clock.getTime() < BASELINE_SEC:
            draw_text(win, text, "+")
            keys = event.getKeys()
            check_exit(keys, win)

        # ======================
        # CUE
        # ======================
        ts = send_marker(outlet, MARKERS["cue"])
        log.append([ts, trial, "cue_onset", 110])

        clock.reset()

        while clock.getTime() < CUE_SEC:
            remaining = CUE_SEC - clock.getTime()

            if remaining > 7:
                msg = "+"
            else:
                msg = f"{condition.upper()} VIDEO STARTS"

            draw_text(win, text, msg)

            keys = event.getKeys()
            check_exit(keys, win)

        # ======================
        # STIMULUS
        # ======================
        ts = send_marker(outlet, MARKERS["stimulus"])
        log.append([ts, trial, "stimulus_start", 120])

        clock.reset()

        while clock.getTime() < STIMULUS_SEC:
            draw_text(win, text, f"{condition.upper()} VIDEO")

            keys = event.getKeys()
            check_exit(keys, win)

            if 's' in keys:
                ts = send_marker(outlet, MARKERS["stress_peak"])
                log.append([ts, trial, "stress_peak", 150])

            if 'n' in keys:
                ts = send_marker(outlet, MARKERS["non_stress"])
                log.append([ts, trial, "non_stress", 160])

            if 'a' in keys:
                ts = send_marker(outlet, MARKERS["artifact"])
                log.append([ts, trial, "artifact", 200])

        # ======================
        # VIDEO END
        # ======================
        ts = send_marker(outlet, MARKERS["video_end"])
        log.append([ts, trial, "video_end", 130])

        # ======================
        # REST
        # ======================
        ts = send_marker(outlet, MARKERS["rest"])
        log.append([ts, trial, "rest_start", 140])

        clock.reset()

        while clock.getTime() < REST_SEC:
            draw_text(win, text, "REST")
            keys = event.getKeys()
            check_exit(keys, win)

    # ======================
    # SAVE LOG
    # ======================
    filename = os.path.join(
        OUTPUT_DIR,
        f"{participant}_{condition}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["time", "trial", "event", "code"])
        writer.writerows(log)

    print(f"\nSaved log: {filename}")

    win.close()


# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--participant", "-p", default="P01")
    parser.add_argument("--condition", "-c", choices=["stress", "relax"], default="stress")
    parser.add_argument("--trials", "-n", type=int, default=1)

    args = parser.parse_args()

    run_experiment(
        participant=args.participant,
        condition=args.condition,
        trials=args.trials
    )