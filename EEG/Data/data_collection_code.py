#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EEG Stress / Relax Experiment
==============================

Complete standalone PsychoPy + LSL experiment.

CONDITIONS
----------
1. stress
2. relax

TRIAL STRUCTURE
---------------
Baseline  : 90 seconds
Cue       : 30 seconds
Stimulus  : 150 seconds ACTIVE VIDEO TIME
Rest      : 30 seconds

IMPORTANT RELAX CONDITION
-------------------------
During the RELAX / NON-STRESS video:

    Press G
        ↓
    Pause current non-stress video
        ↓
    Play Peace Video
        ↓
    Peace Video finishes
        ↓
    Resume non-stress video from exact position

The Peace Video duration is NOT counted toward
the 150-second non-stress stimulus duration.

Example:

    Non-stress video played for 83 sec
             ↓
    G pressed
             ↓
    Peace video = 30 sec
             ↓
    Non-stress video resumes at 83 sec
             ↓
    67 sec remaining

LSL MARKERS
-----------
90  = trial_start
100 = baseline_start
110 = cue_start
120 = stimulus_start
130 = video_end
140 = rest_start
150 = stress_peak
160 = non_stress
170 = peace_video_start
171 = peace_video_end
172 = non_stress_video_resume
200 = artifact
250 = experiment_end

KEYS
----
SPACE = Start experiment
ESC   = Quit safely

S     = Stress peak marker
N     = Non-stress marker
A     = Artifact marker
G     = Pause non-stress video and play Peace Video

COMMAND EXAMPLE
---------------
python eeg_stress_relax_experiment.py \
    --participant P01 \
    --condition relax \
    --trials 1 \
    --stimulus-video videos/non_stress.mp4 \
    --peace-video videos/peace.mp4

"""

# ============================================================
# IMPORTS
# ============================================================

import os
import csv
import time
import argparse
import datetime
import traceback

from psychopy import prefs

# ------------------------------------------------------------
# IMPORTANT:
# Set rendering preference BEFORE importing visual.
# ------------------------------------------------------------

prefs.general["winType"] = "pyglet"

from psychopy import visual, core, event

from pylsl import StreamInfo, StreamOutlet


# ============================================================
# CONFIGURATION
# ============================================================

BASELINE_SEC = 90
CUE_SEC = 30
STIMULUS_SEC = 150
REST_SEC = 30

PEACE_VIDEO_FALLBACK_SEC = 30


# ============================================================
# LSL MARKERS
# ============================================================

MARKERS = {

    # Trial / phases
    "trial_start": 90,
    "baseline": 100,
    "cue": 110,
    "stimulus": 120,
    "video_end": 130,
    "rest": 140,

    # Manual events
    "stress_peak": 150,
    "non_stress": 160,

    # Peace video
    "peace_video_start": 170,
    "peace_video_end": 171,
    "non_stress_video_resume": 172,

    # Artifact
    "artifact": 200,

    # Experiment
    "experiment_end": 250,
}


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR = os.path.join(
    os.getcwd(),
    "logs"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# VIDEO DIRECTORY
# ============================================================

DEFAULT_STRESS_VIDEO = os.path.join(
    os.getcwd(),
    "videos",
    "stress.mp4"
)

DEFAULT_NON_STRESS_VIDEO = os.path.join(
    os.getcwd(),
    "videos",
    "non_stress.mp4"
)

DEFAULT_PEACE_VIDEO = os.path.join(
    os.getcwd(),
    "videos",
    "peace.mp4"
)


# ============================================================
# GLOBAL EXIT FLAG
# ============================================================

QUIT_EXPERIMENT = False


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def utc_timestamp():
    """
    Return UTC timestamp as ISO formatted string.
    """
    return datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()


# ============================================================
# LSL FUNCTIONS
# ============================================================

def create_lsl_outlet():
    """
    Create LSL marker outlet.
    """

    info = StreamInfo(
        name="StressMarkers",
        type="Markers",
        channel_count=1,
        nominal_srate=0,
        channel_format="string",
        source_id="stress_exp_v4"
    )

    outlet = StreamOutlet(info)

    print()
    print("========================================")
    print("LSL MARKER STREAM CREATED")
    print("Name      : StressMarkers")
    print("Type      : Markers")
    print("Source ID : stress_exp_v4")
    print("========================================")
    print()

    return outlet


def send_marker(outlet, code):
    """
    Send numeric marker through LSL.

    Marker is transmitted as a string because
    the LSL stream uses string channel format.
    """

    timestamp = utc_timestamp()

    outlet.push_sample([
        str(code)
    ])

    print(
        f"{timestamp} -> LSL Marker {code}"
    )

    return timestamp


# ============================================================
# LOGGING FUNCTIONS
# ============================================================

def add_log(log, timestamp, trial, event_name, code):
    """
    Add one event to experiment log.
    """

    log.append([
        timestamp,
        trial,
        event_name,
        code
    ])


def save_log(
    log,
    participant,
    condition
):
    """
    Save experiment event log as CSV.
    """

    filename = (
        f"{participant}_"
        f"{condition}_"
        f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        f".csv"
    )

    filepath = os.path.join(
        OUTPUT_DIR,
        filename
    )

    with open(
        filepath,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "time",
            "trial",
            "event",
            "code"
        ])

        writer.writerows(log)

    print()
    print("========================================")
    print("LOG SAVED")
    print(filepath)
    print("========================================")
    print()

    return filepath


# ============================================================
# SAFE TEXT CREATION
# ============================================================

def create_safe_text(win):
    """
    Create safe PsychoPy TextStim.

    Uses pixel units to avoid scaling issues.
    """

    try:

        text = visual.TextStim(
            win=win,
            text="",
            color="white",
            height=30,
            font="Arial",
            units="pix",
            wrapWidth=700
        )

        return text

    except Exception as error:

        print(
            "WARNING: TextStim creation failed."
        )

        print(error)

        return None


# ============================================================
# TEXT DISPLAY
# ============================================================

def draw_text(
    win,
    text_obj,
    message
):
    """
    Draw text and flip window.
    """

    if text_obj is not None:

        text_obj.text = message

        text_obj.draw()

    win.flip()


# ============================================================
# EXIT CHECK
# ============================================================

def check_escape(win):
    """
    Check whether ESC was pressed.

    Returns:
        True  = exit requested
        False = continue
    """

    keys = event.getKeys(
        keyList=["escape"]
    )

    if "escape" in keys:

        print()
        print("ESC pressed.")
        print("Stopping experiment safely.")

        win.close()

        core.quit()

        return True

    return False


# ============================================================
# WAIT SCREEN
# ============================================================

def wait_for_start(
    win,
    text_obj,
    participant,
    condition
):
    """
    Display experiment start screen.
    """

    message = (
        f"Participant: {participant}\n"
        f"Condition: {condition.upper()}\n\n"
        f"SPACE = Start\n"
        f"ESC = Quit"
    )

    draw_text(
        win,
        text_obj,
        message
    )

    while True:

        keys = event.waitKeys(
            keyList=[
                "space",
                "escape"
            ]
        )

        if "escape" in keys:

            win.close()

            return False

        if "space" in keys:

            return True


# ============================================================
# PLAY VIDEO
# ============================================================

def create_movie(win, video_path):
    """
    Create PsychoPy movie stimulus.

    Tries MovieStim3 first.

    Falls back to MovieStim if necessary.
    """

    if not os.path.exists(video_path):

        print()
        print("ERROR: Video file not found:")
        print(video_path)
        print()

        return None

    try:

        print(
            f"Loading video:\n{video_path}"
        )

        # ----------------------------------------------------
        # Try MovieStim3
        # ----------------------------------------------------

        if hasattr(
            visual,
            "MovieStim3"
        ):

            movie = visual.MovieStim3(
                win=win,
                filename=video_path,
                loop=False,
                noAudio=False,
                size=(
                    win.size[0],
                    win.size[1]
                )
            )

        else:

            # ------------------------------------------------
            # Fallback
            # ------------------------------------------------

            movie = visual.MovieStim(
                win=win,
                filename=video_path,
                loop=False,
                noAudio=False,
                size=(
                    win.size[0],
                    win.size[1]
                )
            )

        print("Video loaded successfully.")

        return movie

    except Exception as error:

        print()
        print("ERROR: Could not load video.")
        print(video_path)
        print()
        print(error)
        print()

        traceback.print_exc()

        return None


# ============================================================
# GET MOVIE DURATION
# ============================================================

def get_movie_duration(movie):
    """
    Try to obtain video duration.

    Returns None if unavailable.
    """

    try:

        duration = movie.duration

        if duration is not None:

            return float(duration)

    except Exception:
        pass

    return None


# ============================================================
# RESET MOVIE
# ============================================================

def reset_movie(movie):
    """
    Reset movie to beginning.
    """

    if movie is None:
        return

    try:

        movie.seek(0)

    except Exception:

        try:

            movie.stop()

        except Exception:
            pass


# ============================================================
# PLAY PEACE VIDEO
# ============================================================

def play_peace_video(
    win,
    text_obj,
    peace_movie,
    outlet,
    log,
    trial
):
    """
    Play Peace Video completely.

    The non-stress active-time counter is NOT
    increased during this function.

    Returns:
        True  = Peace video completed
        False = user requested exit
    """

    # --------------------------------------------------------
    # Marker: Peace Video Start
    # --------------------------------------------------------

    ts = send_marker(
        outlet,
        MARKERS["peace_video_start"]
    )

    add_log(
        log,
        ts,
        trial,
        "peace_video_start",
        MARKERS["peace_video_start"]
    )

    print()
    print("----------------------------------------")
    print("PEACE VIDEO START")
    print("----------------------------------------")

    # --------------------------------------------------------
    # If Peace Video exists
    # --------------------------------------------------------

    if peace_movie is not None:

        reset_movie(
            peace_movie
        )

        peace_movie.play()

        peace_clock = core.Clock()
        peace_clock.reset()

        while True:

            # -----------------------------------------------
            # Check ESC
            # -----------------------------------------------

            keys = event.getKeys()

            if "escape" in keys:

                try:
                    peace_movie.stop()
                except Exception:
                    pass

                win.close()
                core.quit()

                return False

            # -----------------------------------------------
            # Draw movie
            # -----------------------------------------------

            try:

                peace_movie.draw()

                win.flip()

            except Exception as error:

                print(
                    "Peace video playback error:"
                )

                print(error)

                break

            # -----------------------------------------------
            # Check whether movie has ended
            # -----------------------------------------------

            try:

                status = peace_movie.status

                if status == visual.FINISHED:
                    break

            except Exception:

                duration = get_movie_duration(
                    peace_movie
                )

                if (
                    duration is not None
                    and
                    peace_clock.getTime() >= duration
                ):
                    break

            # Safety fallback
            duration = get_movie_duration(
                peace_movie
            )

            if (
                duration is not None
                and
                peace_clock.getTime() >= duration + 1
            ):
                break

        try:
            peace_movie.stop()
        except Exception:
            pass

    # --------------------------------------------------------
    # Fallback if no movie
    # --------------------------------------------------------

    else:

        print(
            "WARNING: Peace video unavailable."
        )

        print(
            f"Showing fallback screen for "
            f"{PEACE_VIDEO_FALLBACK_SEC} seconds."
        )

        fallback_clock = core.Clock()
        fallback_clock.reset()

        while (
            fallback_clock.getTime()
            < PEACE_VIDEO_FALLBACK_SEC
        ):

            draw_text(
                win,
                text_obj,
                "PEACE / RELAX"
            )

            if check_escape(win):
                return False

    # --------------------------------------------------------
    # Marker: Peace Video End
    # --------------------------------------------------------

    ts = send_marker(
        outlet,
        MARKERS["peace_video_end"]
    )

    add_log(
        log,
        ts,
        trial,
        "peace_video_end",
        MARKERS["peace_video_end"]
    )

    print("----------------------------------------")
    print("PEACE VIDEO END")
    print("----------------------------------------")

    return True


# ============================================================
# STIMULUS VIDEO
# ============================================================

def run_stimulus_video(
    win,
    text_obj,
    stimulus_movie,
    peace_movie,
    outlet,
    log,
    trial,
    condition
):
    """
    Run the main stimulus video.

    For RELAX condition:
        G = pause stimulus
            -> play peace video
            -> resume stimulus

    IMPORTANT:
    The 150-second timer measures only
    ACTIVE stimulus-video time.

    Peace-video time is excluded.
    """

    # --------------------------------------------------------
    # Experiment active-time tracking
    # --------------------------------------------------------

    active_stimulus_start = time.perf_counter()

    paused_total = 0.0

    # --------------------------------------------------------
    # Prepare stimulus movie
    # --------------------------------------------------------

    if stimulus_movie is not None:

        reset_movie(
            stimulus_movie
        )

        stimulus_movie.play()

    else:

        print(
            "WARNING: Main stimulus video unavailable."
        )

    # --------------------------------------------------------
    # Main active stimulus loop
    # --------------------------------------------------------

    while True:

        # ----------------------------------------------------
        # Calculate ACTIVE stimulus time
        #
        # Actual wall-clock time:
        #
        # current - start
        #
        # minus all Peace-video pauses.
        # ----------------------------------------------------

        active_elapsed = (
            time.perf_counter()
            - active_stimulus_start
            - paused_total
        )

        # ----------------------------------------------------
        # End condition
        # ----------------------------------------------------

        if active_elapsed >= STIMULUS_SEC:

            break

        # ----------------------------------------------------
        # KEYBOARD EVENTS
        # ----------------------------------------------------

        keys = event.getKeys()

        # ----------------------------------------------------
        # ESC
        # ----------------------------------------------------

        if "escape" in keys:

            try:

                if stimulus_movie:
                    stimulus_movie.stop()

            except Exception:
                pass

            win.close()
            core.quit()

            return False

        # ----------------------------------------------------
        # G = PEACE VIDEO
        # ----------------------------------------------------

        if (
            condition == "relax"
            and
            "g" in keys
        ):

            # ================================================
            # EXACT ACTIVE POSITION BEFORE PAUSE
            # ================================================

            paused_at = active_elapsed

            print()
            print("========================================")
            print("G PRESSED")
            print("NON-STRESS VIDEO PAUSED")
            print(
                f"Active position: "
                f"{paused_at:.3f} seconds"
            )
            print(
                f"Remaining: "
                f"{STIMULUS_SEC - paused_at:.3f} seconds"
            )
            print("========================================")
            print()

            # ------------------------------------------------
            # Pause Main Video
            # ------------------------------------------------

            try:

                if stimulus_movie is not None:
                    stimulus_movie.pause()

            except Exception as error:

                print(
                    "Could not pause main video:"
                )

                print(error)

            # ------------------------------------------------
            # Start measuring Peace Video pause
            # ------------------------------------------------

            peace_start_wallclock = (
                time.perf_counter()
            )

            # ------------------------------------------------
            # Play Peace Video
            # ------------------------------------------------

            peace_completed = play_peace_video(
                win=win,
                text_obj=text_obj,
                peace_movie=peace_movie,
                outlet=outlet,
                log=log,
                trial=trial
            )

            if not peace_completed:

                return False

            # ------------------------------------------------
            # Measure Peace Video duration
            # ------------------------------------------------

            peace_duration = (
                time.perf_counter()
                - peace_start_wallclock
            )

            # ------------------------------------------------
            # Add Peace duration to pause total
            # ------------------------------------------------

            paused_total += peace_duration

            print()
            print("========================================")
            print("RESUMING NON-STRESS VIDEO")
            print(
                f"Paused at: "
                f"{paused_at:.3f} seconds"
            )
            print(
                f"Peace duration: "
                f"{peace_duration:.3f} seconds"
            )
            print(
                f"Total pause: "
                f"{paused_total:.3f} seconds"
            )
            print(
                f"Remaining stimulus time: "
                f"{STIMULUS_SEC - paused_at:.3f} seconds"
            )
            print("========================================")
            print()

            # ------------------------------------------------
            # Resume Main Video
            # ------------------------------------------------

            try:

                if stimulus_movie is not None:

                    stimulus_movie.play()

            except Exception as error:

                print(
                    "Could not resume main video:"
                )

                print(error)

            # ------------------------------------------------
            # Resume Marker
            # ------------------------------------------------

            ts = send_marker(
                outlet,
                MARKERS[
                    "non_stress_video_resume"
                ]
            )

            add_log(
                log,
                ts,
                trial,
                "non_stress_video_resume",
                MARKERS[
                    "non_stress_video_resume"
                ]
            )

            # ------------------------------------------------
            # IMPORTANT
            #
            # Continue loop without resetting
            # active_stimulus_start.
            #
            # paused_total compensates for the
            # Peace Video duration.
            # ------------------------------------------------

            continue

        # ----------------------------------------------------
        # S = STRESS PEAK
        # ----------------------------------------------------

        if "s" in keys:

            ts = send_marker(
                outlet,
                MARKERS["stress_peak"]
            )

            add_log(
                log,
                ts,
                trial,
                "stress_peak",
                MARKERS["stress_peak"]
            )

        # ----------------------------------------------------
        # N = NON-STRESS
        # ----------------------------------------------------

        if "n" in keys:

            ts = send_marker(
                outlet,
                MARKERS["non_stress"]
            )

            add_log(
                log,
                ts,
                trial,
                "non_stress",
                MARKERS["non_stress"]
            )

        # ----------------------------------------------------
        # A = ARTIFACT
        # ----------------------------------------------------

        if "a" in keys:

            ts = send_marker(
                outlet,
                MARKERS["artifact"]
            )

            add_log(
                log,
                ts,
                trial,
                "artifact",
                MARKERS["artifact"]
            )

        # ----------------------------------------------------
        # Draw Main Stimulus Video
        # ----------------------------------------------------

        if stimulus_movie is not None:

            try:

                stimulus_movie.draw()

                win.flip()

            except Exception as error:

                print()
                print(
                    "Stimulus video playback error:"
                )

                print(error)

                draw_text(
                    win,
                    text_obj,
                    f"{condition.upper()} VIDEO"
                )

        else:

            draw_text(
                win,
                text_obj,
                f"{condition.upper()} VIDEO"
            )

    # --------------------------------------------------------
    # Stop Main Video
    # --------------------------------------------------------

    try:

        if stimulus_movie is not None:
            stimulus_movie.stop()

    except Exception:
        pass

    print()
    print("Stimulus active time completed:")
    print(
        f"{STIMULUS_SEC:.2f} seconds"
    )

    print(
        f"Total Peace pause time: "
        f"{paused_total:.2f} seconds"
    )

    print()

    return True


# ============================================================
# BASELINE
# ============================================================

def run_baseline(
    win,
    text_obj,
    outlet,
    log,
    trial
):
    """
    Run baseline phase.
    """

    ts = send_marker(
        outlet,
        MARKERS["baseline"]
    )

    add_log(
        log,
        ts,
        trial,
        "baseline_start",
        MARKERS["baseline"]
    )

    print(
        f"Baseline started: "
        f"{BASELINE_SEC} seconds"
    )

    clock = core.Clock()
    clock.reset()

    while clock.getTime() < BASELINE_SEC:

        draw_text(
            win,
            text_obj,
            "+"
        )

        if check_escape(win):
            return False

    return True


# ============================================================
# CUE
# ============================================================

def run_cue(
    win,
    text_obj,
    outlet,
    log,
    trial,
    condition
):
    """
    Run cue phase.
    """

    ts = send_marker(
        outlet,
        MARKERS["cue"]
    )

    add_log(
        log,
        ts,
        trial,
        "cue_onset",
        MARKERS["cue"]
    )

    print(
        f"Cue started: "
        f"{CUE_SEC} seconds"
    )

    clock = core.Clock()
    clock.reset()

    while clock.getTime() < CUE_SEC:

        remaining = (
            CUE_SEC
            - clock.getTime()
        )

        if remaining > 7:

            message = "+"

        else:

            message = (
                f"{condition.upper()} "
                f"VIDEO STARTS"
            )

        draw_text(
            win,
            text_obj,
            message
        )

        if check_escape(win):
            return False

    return True


# ============================================================
# REST
# ============================================================

def run_rest(
    win,
    text_obj,
    outlet,
    log,
    trial
):
    """
    Run rest phase.
    """

    ts = send_marker(
        outlet,
        MARKERS["rest"]
    )

    add_log(
        log,
        ts,
        trial,
        "rest_start",
        MARKERS["rest"]
    )

    print(
        f"Rest started: "
        f"{REST_SEC} seconds"
    )

    clock = core.Clock()
    clock.reset()

    while clock.getTime() < REST_SEC:

        draw_text(
            win,
            text_obj,
            "REST"
        )

        if check_escape(win):
            return False

    return True


# ============================================================
# CREATE WINDOW
# ============================================================

def create_window():
    """
    Create safe PsychoPy window.
    """

    print(
        "Creating PsychoPy window..."
    )

    win = visual.Window(
        size=(800, 600),
        fullscr=False,
        screen=0,
        winType="pyglet",
        allowGUI=True,
        monitor="testMonitor",
        units="pix",
        color="black"
    )

    return win


# ============================================================
# RUN ONE TRIAL
# ============================================================

def run_trial(
    win,
    text_obj,
    outlet,
    log,
    trial,
    condition,
    stimulus_video_path,
    peace_video_path
):
    """
    Run one complete trial.
    """

    print()
    print()
    print("########################################")
    print(
        f"TRIAL {trial} START"
    )
    print("########################################")
    print()

    # --------------------------------------------------------
    # Trial Start
    # --------------------------------------------------------

    ts = send_marker(
        outlet,
        MARKERS["trial_start"]
    )

    add_log(
        log,
        ts,
        trial,
        "trial_start",
        MARKERS["trial_start"]
    )

    # --------------------------------------------------------
    # Baseline
    # --------------------------------------------------------

    if not run_baseline(
        win,
        text_obj,
        outlet,
        log,
        trial
    ):

        return False

    # --------------------------------------------------------
    # Cue
    # --------------------------------------------------------

    if not run_cue(
        win,
        text_obj,
        outlet,
        log,
        trial,
        condition
    ):

        return False

    # --------------------------------------------------------
    # Stimulus marker
    # --------------------------------------------------------

    ts = send_marker(
        outlet,
        MARKERS["stimulus"]
    )

    add_log(
        log,
        ts,
        trial,
        "stimulus_start",
        MARKERS["stimulus"]
    )

    # --------------------------------------------------------
    # Load stimulus video
    # --------------------------------------------------------

    stimulus_movie = create_movie(
        win,
        stimulus_video_path
    )

    # --------------------------------------------------------
    # Load peace video
    #
    # Only needed for relax condition.
    # --------------------------------------------------------

    peace_movie = None

    if condition == "relax":

        peace_movie = create_movie(
            win,
            peace_video_path
        )

    # --------------------------------------------------------
    # Run stimulus
    # --------------------------------------------------------

    success = run_stimulus_video(
        win=win,
        text_obj=text_obj,
        stimulus_movie=stimulus_movie,
        peace_movie=peace_movie,
        outlet=outlet,
        log=log,
        trial=trial,
        condition=condition
    )

    # --------------------------------------------------------
    # Clean up movies
    # --------------------------------------------------------

    try:

        if stimulus_movie is not None:
            stimulus_movie.stop()

    except Exception:
        pass

    try:

        if peace_movie is not None:
            peace_movie.stop()

    except Exception:
        pass

    if not success:

        return False

    # --------------------------------------------------------
    # Video End
    # --------------------------------------------------------

    ts = send_marker(
        outlet,
        MARKERS["video_end"]
    )

    add_log(
        log,
        ts,
        trial,
        "video_end",
        MARKERS["video_end"]
    )

    # --------------------------------------------------------
    # Rest
    # --------------------------------------------------------

    if not run_rest(
        win,
        text_obj,
        outlet,
        log,
        trial
    ):

        return False

    print()
    print(
        f"TRIAL {trial} COMPLETED"
    )
    print()

    return True


# ============================================================
# MAIN EXPERIMENT
# ============================================================

def run_experiment(
    participant,
    condition,
    trials,
    stimulus_video_path,
    peace_video_path
):
    """
    Main experiment controller.
    """

    print()
    print("========================================")
    print("EEG STRESS / RELAX EXPERIMENT")
    print("========================================")
    print(
        f"Participant : {participant}"
    )
    print(
        f"Condition   : {condition}"
    )
    print(
        f"Trials      : {trials}"
    )
    print("========================================")
    print()

    # --------------------------------------------------------
    # Create LSL outlet
    # --------------------------------------------------------

    outlet = create_lsl_outlet()

    # --------------------------------------------------------
    # Create PsychoPy window
    # --------------------------------------------------------

    win = create_window()

    # --------------------------------------------------------
    # Create text stimulus
    # --------------------------------------------------------

    text = create_safe_text(
        win
    )

    # --------------------------------------------------------
    # Event log
    # --------------------------------------------------------

    log = []

    try:

        # ====================================================
        # START SCREEN
        # ====================================================

        started = wait_for_start(
            win=win,
            text_obj=text,
            participant=participant,
            condition=condition
        )

        if not started:

            win.close()

            return

        # ====================================================
        # RUN TRIALS
        # ====================================================

        for trial in range(
            1,
            trials + 1
        ):

            success = run_trial(
                win=win,
                text_obj=text,
                outlet=outlet,
                log=log,
                trial=trial,
                condition=condition,
                stimulus_video_path=stimulus_video_path,
                peace_video_path=peace_video_path
            )

            if not success:

                break

        # ====================================================
        # EXPERIMENT END
        # ====================================================

        ts = send_marker(
            outlet,
            MARKERS["experiment_end"]
        )

        add_log(
            log,
            ts,
            0,
            "experiment_end",
            MARKERS["experiment_end"]
        )

        # ====================================================
        # SAVE LOG
        # ====================================================

        save_log(
            log=log,
            participant=participant,
            condition=condition
        )

    except Exception as error:

        print()
        print("========================================")
        print("EXPERIMENT ERROR")
        print("========================================")
        print(error)
        print()

        traceback.print_exc()

        # Try saving log even if experiment crashes
        try:

            save_log(
                log=log,
                participant=participant,
                condition=condition
            )

        except Exception:

            pass

    finally:

        # ====================================================
        # CLEANUP
        # ====================================================

        print()
        print(
            "Closing experiment..."
        )

        try:
            win.close()
        except Exception:
            pass

        core.quit()


# ============================================================
# COMMAND LINE
# ============================================================

def parse_arguments():
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "EEG Stress / Relax "
            "PsychoPy Experiment"
        )
    )

    parser.add_argument(
        "--participant",
        "-p",
        type=str,
        default="P01",
        help="Participant ID"
    )

    parser.add_argument(
        "--condition",
        "-c",
        type=str,
        choices=[
            "stress",
            "relax"
        ],
        default="stress",
        help="Experiment condition"
    )

    parser.add_argument(
        "--trials",
        "-n",
        type=int,
        default=1,
        help="Number of trials"
    )

    parser.add_argument(
        "--stimulus-video",
        type=str,
        default=None,
        help=(
            "Path to stress/non-stress "
            "stimulus video"
        )
    )

    parser.add_argument(
        "--peace-video",
        type=str,
        default=None,
        help=(
            "Path to peace video "
            "used during relax condition"
        )
    )

    return parser.parse_args()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    args = parse_arguments()

    # --------------------------------------------------------
    # Select stimulus video
    # --------------------------------------------------------

    if args.stimulus_video:

        stimulus_video = (
            os.path.abspath(
                args.stimulus_video
            )
        )

    else:

        if args.condition == "stress":

            stimulus_video = (
                DEFAULT_STRESS_VIDEO
            )

        else:

            stimulus_video = (
                DEFAULT_NON_STRESS_VIDEO
            )

    # --------------------------------------------------------
    # Select peace video
    # --------------------------------------------------------

    if args.peace_video:

        peace_video = (
            os.path.abspath(
                args.peace_video
            )
        )

    else:

        peace_video = (
            DEFAULT_PEACE_VIDEO
        )

    # --------------------------------------------------------
    # Print files
    # --------------------------------------------------------

    print()
    print("VIDEO CONFIGURATION")
    print("----------------------------------------")
    print(
        f"Stimulus video : "
        f"{stimulus_video}"
    )

    if args.condition == "relax":

        print(
            f"Peace video    : "
            f"{peace_video}"
        )

    print("----------------------------------------")
    print()

    # --------------------------------------------------------
    # Run
    # --------------------------------------------------------

    run_experiment(
        participant=args.participant,
        condition=args.condition,
        trials=args.trials,
        stimulus_video_path=stimulus_video,
        peace_video_path=peace_video
    )