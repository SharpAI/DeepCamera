#!/usr/bin/env python3
"""
Temporal multi-object tracker for the YOLO 2026 detection skill.

YOLO runs independently on every frame, so an object that is detected at 0.55
confidence one frame and 0.45 the next makes its box blink on and off. This
module turns those noisy per-frame detections into smooth, persistent tracks.

Techniques (one tracker instance per camera):

  * Kalman filter (constant-velocity, SORT-style 7D state) per track — smooths
    box jitter and, when a detection is briefly missed, PREDICTS where the object
    is so the box keeps following it instead of vanishing ("coasting").
  * Two-stage IoU association (ByteTrack-style): high-confidence detections are
    matched first, then a SECOND pass lets an existing track be sustained by a
    LOW-confidence detection it would otherwise be filtered out — i.e. confidence
    hysteresis, which is what actually kills the on/off flicker.
  * Confirmation (n_init): a brand-new detection must persist for a few frames
    before it is emitted, suppressing single-frame false-positive flicker.
  * Coasting: a confirmed track survives up to max_age missed frames (emitting
    the Kalman-predicted box) before being dropped.
  * Off-screen deletion: once a track's predicted box leaves the frame it is
    removed immediately — a person walking out does NOT leave a ghost box.
  * Scene-change hold: if the WHOLE frame changes abruptly (camera covered,
    lights switched) the detections are unreliable, so tracks are frozen on their
    last box instead of being aged out; they re-acquire when the scene settles.

Pure numpy — no scipy/filterpy. Greedy association is used (fine for the handful
of objects a security camera sees).
"""

from __future__ import annotations

import numpy as np


# ───────────────────────────────────────────────────────────────────────────────
# Geometry helpers
# ───────────────────────────────────────────────────────────────────────────────

def _bbox_to_z(bbox):
    """[x1,y1,x2,y2] → measurement [cx, cy, s, r] (center, area, aspect)."""
    w = max(1e-6, bbox[2] - bbox[0])
    h = max(1e-6, bbox[3] - bbox[1])
    cx = bbox[0] + w / 2.0
    cy = bbox[1] + h / 2.0
    s = w * h          # scale (area)
    r = w / h          # aspect ratio
    return np.array([cx, cy, s, r], dtype=np.float64).reshape((4, 1))


def _z_to_bbox(x):
    """State [cx, cy, s, r, ...] → [x1,y1,x2,y2]."""
    s = max(1e-6, float(x[2]))
    r = max(1e-6, float(x[3]))
    w = np.sqrt(s * r)
    h = s / w
    cx, cy = float(x[0]), float(x[1])
    return [cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0]


def iou(a, b):
    """IoU of two [x1,y1,x2,y2] boxes."""
    xx1 = max(a[0], b[0]); yy1 = max(a[1], b[1])
    xx2 = min(a[2], b[2]); yy2 = min(a[3], b[3])
    w = max(0.0, xx2 - xx1); h = max(0.0, yy2 - yy1)
    inter = w * h
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


# ───────────────────────────────────────────────────────────────────────────────
# Kalman box tracker (constant-velocity, SORT 7D state: [cx,cy,s,r,vcx,vcy,vs])
# ───────────────────────────────────────────────────────────────────────────────

class _KalmanBoxTracker:
    def __init__(self, bbox, cls_name, conf):
        ndim = 7
        # State transition (constant velocity on cx, cy, s)
        self.F = np.eye(ndim)
        for i in range(3):
            self.F[i, i + 4] = 1.0
        # Measurement matrix (observe cx, cy, s, r)
        self.H = np.zeros((4, ndim))
        for i in range(4):
            self.H[i, i] = 1.0

        # Covariances (SORT defaults — give velocities high initial uncertainty)
        self.P = np.eye(ndim) * 10.0
        self.P[4:, 4:] *= 1000.0
        self.R = np.eye(4)
        self.R[2:, 2:] *= 10.0
        self.Q = np.eye(ndim)
        self.Q[-1, -1] *= 0.01
        self.Q[4:, 4:] *= 0.01

        self.x = np.zeros((ndim, 1))
        self.x[:4] = _bbox_to_z(bbox)

        self.cls_name = cls_name
        self.conf = float(conf)
        self.time_since_update = 0   # frames since a real detection updated us
        self.hits = 1                # total detections matched
        self.hit_streak = 1          # consecutive recent hits
        self.age = 0                 # total frames alive

    def predict(self):
        # Guard: don't let area go negative during long coasting
        if self.x[6] + self.x[2] <= 0:
            self.x[6] *= 0.0
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        return _z_to_bbox(self.x)

    def update(self, bbox, cls_name, conf):
        self.time_since_update = 0
        self.hits += 1
        self.hit_streak += 1
        z = _bbox_to_z(bbox)
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        self.P = (np.eye(self.P.shape[0]) - K @ self.H) @ self.P
        # Smooth confidence; let the class follow the latest strong detection
        self.conf = 0.6 * self.conf + 0.4 * float(conf)
        self.cls_name = cls_name

    def bbox(self):
        return _z_to_bbox(self.x)


# ───────────────────────────────────────────────────────────────────────────────
# Scene-change detector — flags frames where the WHOLE image changed abruptly
# (camera covered/uncovered, lights toggled) so we don't drop tracks on garbage.
# ───────────────────────────────────────────────────────────────────────────────

class _SceneChangeDetector:
    def __init__(self, threshold=0.45, grid=16):
        self.threshold = threshold
        self.grid = grid
        self._prev = None

    def is_disrupted(self, frame_img):
        """frame_img: HxWx3 uint8 (BGR/RGB both fine). Returns True on abrupt
        global change. Cheap: mean-abs-diff of a 16x16 grayscale thumbnail."""
        if frame_img is None:
            return False
        try:
            img = np.asarray(frame_img)
            if img.ndim == 3:
                img = img.mean(axis=2)
            h, w = img.shape[:2]
            gh = max(1, h // self.grid); gw = max(1, w // self.grid)
            small = img[: gh * self.grid: gh, : gw * self.grid: gw].astype(np.float64)
        except Exception:
            return False
        disrupted = False
        if self._prev is not None and self._prev.shape == small.shape:
            mad = np.abs(small - self._prev).mean() / 255.0
            disrupted = mad > self.threshold
        self._prev = small
        return disrupted


# ───────────────────────────────────────────────────────────────────────────────
# Multi-object tracker (one per camera)
# ───────────────────────────────────────────────────────────────────────────────

class MultiObjectTracker:
    """
    Per-camera tracker. Feed it the raw YOLO detections for a frame and it
    returns smoothed, persistent tracks.

    Params:
      max_age:         frames a confirmed track may coast (no detection) before
                       it's dropped.
      n_init:          consecutive hits a new track needs before it's emitted.
      iou_high:        IoU needed to match a high-confidence detection.
      iou_low:         IoU needed in the second (low-confidence recovery) pass.
      conf_high:       detections >= this are "high confidence" (stage 1).
      edge_margin:     fraction of frame size; a coasting track whose predicted
                       center is within this margin of the border AND moving
                       outward is treated as having left → deleted immediately.
      max_disrupted:   max consecutive disrupted (scene-change) frames to hold
                       tracks frozen before giving up.
    """

    def __init__(self, max_age=15, n_init=3, iou_high=0.3, iou_low=0.2,
                 conf_high=0.4, edge_margin=0.02, max_disrupted=30,
                 scene_threshold=0.45):
        self.max_age = max_age
        self.n_init = n_init
        self.iou_high = iou_high
        self.iou_low = iou_low
        self.conf_high = conf_high
        self.edge_margin = edge_margin
        self.max_disrupted = max_disrupted
        self.tracks: list[_KalmanBoxTracker] = []
        self.scene = _SceneChangeDetector(threshold=scene_threshold)
        self._holding = False    # in a scene-disruption hold (don't age tracks)
        self._hold_count = 0     # frames spent in the current hold
        self._next_id = 1
        self._ids: dict[int, int] = {}   # id(track) → public track_id

    # ── association (greedy, class-aware) ──
    def _match(self, dets, det_boxes, track_idx, det_idx, iou_thresh):
        """Greedily match tracks[track_idx] to dets[det_idx] by IoU (same class
        only). Returns (matches, unmatched_tracks, unmatched_dets)."""
        pairs = []
        for ti in track_idx:
            tb = self.tracks[ti].bbox()
            tcls = self.tracks[ti].cls_name
            for di in det_idx:
                if dets[di]["class"] != tcls:
                    continue
                v = iou(tb, det_boxes[di])
                if v >= iou_thresh:
                    pairs.append((v, ti, di))
        pairs.sort(reverse=True)  # best IoU first
        matches = []
        used_t, used_d = set(), set()
        for _, ti, di in pairs:
            if ti in used_t or di in used_d:
                continue
            used_t.add(ti); used_d.add(di)
            matches.append((ti, di))
        un_t = [ti for ti in track_idx if ti not in used_t]
        un_d = [di for di in det_idx if di not in used_d]
        return matches, un_t, un_d

    def update(self, detections, frame_w, frame_h, frame_img=None):
        """
        detections: list of {"class": str, "confidence": float,
                              "bbox": [x1,y1,x2,y2]}
        Returns list of {"class","confidence","bbox","track_id","coasting"}.
        """
        disrupted = self.scene.is_disrupted(frame_img)

        # 1) Predict every track forward.
        for t in self.tracks:
            t.predict()

        det_boxes = [d["bbox"] for d in detections]

        # 2) Associate (always — even while holding — so a held track re-acquires
        #    the moment the real detection comes back). Two-stage: high-confidence
        #    first, then low-confidence to SUSTAIN existing tracks (hysteresis).
        all_t = list(range(len(self.tracks)))
        all_d = list(range(len(detections)))
        hi_d = [i for i in all_d if detections[i]["confidence"] >= self.conf_high]
        lo_d = [i for i in all_d if i not in hi_d]
        m1, un_t1, un_hi = self._match(detections, det_boxes, all_t, hi_d, self.iou_high)
        m2, un_t2, _un_lo = self._match(detections, det_boxes, un_t1, lo_d, self.iou_low)
        matches = m1 + m2
        for ti, di in matches:
            d = detections[di]
            self.tracks[ti].update(d["bbox"], d["class"], d["confidence"])

        # 3) Scene-disruption "hold" state machine. While holding, unmatched tracks
        #    are NOT aged out — a covered/flashed camera legitimately shows nothing,
        #    so absence of detections is not evidence the object left. Holding ends
        #    the instant detections re-associate (sensor recovered) or after
        #    max_disrupted frames (camera left covered for good).
        if disrupted:
            self._holding = True
            self._hold_count = 0
        if self._holding:
            self._hold_count += 1
            if matches or self._hold_count > self.max_disrupted:
                self._holding = False

        # 4) Spawn new tracks from confident, unmatched detections — but not during
        #    an active disruption frame (its detections may be garbage).
        if not disrupted:
            for di in un_hi:
                d = detections[di]
                self.tracks.append(_KalmanBoxTracker(d["bbox"], d["class"], d["confidence"]))

        # 5) Decay confidence on coasting tracks (signals growing uncertainty),
        #    except while holding (the object isn't gone, the sensor is blocked).
        if not self._holding:
            for t in self.tracks:
                if t.time_since_update > 0:
                    t.conf *= 0.9

        # 6) Lifecycle: drop dead / off-screen tracks; build output.
        kept = []
        output = []
        for t in self.tracks:
            box = t.bbox()
            coasting = t.time_since_update > 0

            # Off-screen: a coasting track whose center has left the frame walked
            # off — delete, never persist a ghost box. Suppressed while holding
            # (a covered camera gives no reliable position to judge "left").
            cx = (box[0] + box[2]) / 2.0
            cy = (box[1] + box[3]) / 2.0
            mx = self.edge_margin * frame_w
            my = self.edge_margin * frame_h
            off_screen = (cx < mx or cx > frame_w - mx or
                          cy < my or cy > frame_h - my)
            if coasting and off_screen and not self._holding:
                continue  # drop

            # Age out coasting tracks past max_age — unless the sensor is disrupted.
            if t.time_since_update > self.max_age and not self._holding:
                continue  # drop

            kept.append(t)

            # Anti-flicker-ON: never emit a track until it has been seen n_init
            # times. A single-frame false positive is therefore never shown.
            if t.hits < self.n_init:
                continue

            tid = self._ids.get(id(t))
            if tid is None:
                tid = self._next_id; self._next_id += 1
                self._ids[id(t)] = tid

            x1, y1, x2, y2 = box
            output.append({
                "class": t.cls_name,
                "confidence": round(max(0.0, min(1.0, t.conf)), 3),
                "bbox": [int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))],
                "track_id": tid,
                "coasting": coasting,
            })

        # prune id map for dropped tracks
        alive = {id(t) for t in kept}
        self._ids = {k: v for k, v in self._ids.items() if k in alive}
        self.tracks = kept
        return output
