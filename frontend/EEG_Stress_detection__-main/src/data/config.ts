// ─────────────────────────────────────────────────────────────────────
// Central data configuration — edit values here to update the site.
// Placeholder values use "—" for metrics that haven't been measured yet.
// ─────────────────────────────────────────────────────────────────────

export type Dataset = {
  id: string;
  number: string;
  name: string;
  signalType: 'ECG' | 'EEG' | 'Other';
  accent: 'signal' | 'bio' | 'violet';
  description: string;
  purpose: string;
  pipeline: string[];
  approach: string;
  details: { label: string; value: string }[];
};

export const datasets: Dataset[] = [
  {
    id: 'deap',
    number: '01',
    name: 'DEAP Dataset',
    signalType: 'EEG',
    accent: 'bio',
    description:
      'Database for Emotion Analysis using Physiological Signals — 32-channel EEG recordings from 32 participants watching 40 music videos with valence/arousal/dominance/liking ratings.',
    purpose: 'Detect stress and emotional states from EEG brain activity patterns using standardised benchmark data.',
    pipeline: ['Raw EEG', 'Artifact removal', 'Bandpass (1–50 Hz)', 'Epoching', 'Band-power features', 'SVM Classification'],
    approach: 'SVM with RBF kernel trained on mean band-power features per channel for binary stress classification.',
    details: [
      { label: 'Signal type', value: 'EEG — Brain electrical activity' },
      { label: 'Channels', value: '32' },
      { label: 'Participants', value: '32' },
      { label: 'Trials', value: '40 per subject' },
      { label: 'Sampling rate', value: '128 Hz' },
    ],
  },
  {
    id: 'custom',
    number: '02',
    name: 'Custom Collected Dataset',
    signalType: 'EEG',
    accent: 'signal',
    description:
      'Self-collected EEG stress data from 15 participants using XDF format. Includes resting-state and stress-induction task recordings for real-world stress detection evaluation.',
    purpose: 'Validate stress detection models on locally acquired data with controlled stress and relaxed conditions.',
    pipeline: ['XDF Import', 'Artifact removal', 'Bandpass (1–50 Hz)', 'Epoching', 'Feature extraction', 'Model Evaluation'],
    approach: 'Cross-dataset evaluation comparing model performance between benchmark DEAP and real-world collected signals.',
    details: [
      { label: 'Signal type', value: 'EEG — Brain electrical activity' },
      { label: 'Channels', value: '—' },
      { label: 'Participants', value: '15' },
      { label: 'Format', value: 'XDF' },
      { label: 'Sampling rate', value: '—' },
    ],
  },
];

// ── Pipeline stages ──────────────────────────────────────────────
export const pipelineStages = [
  { id: 'raw', label: 'Raw Signal', detail: 'Acquire physiological data from sensors' },
  { id: 'clean', label: 'Data Cleaning', detail: 'Remove artifacts and corrupted segments' },
  { id: 'noise', label: 'Noise Removal', detail: 'Suppress baseline wander and powerline noise' },
  { id: 'filter', label: 'Filtering', detail: 'Bandpass filtering to isolate signal band of interest' },
  { id: 'segment', label: 'Segmentation', detail: 'Window signals into analysis epochs' },
  { id: 'feature', label: 'Feature Extraction', detail: 'Derive time, frequency, and morphological features' },
  { id: 'train', label: 'Model Training', detail: 'Train ML/DL models on extracted features' },
  { id: 'predict', label: 'Prediction', detail: 'Generate classifications on unseen signals' },
  { id: 'eval', label: 'Evaluation', detail: 'Assess performance with held-out test data' },
];

// ── Architecture flow ──────────────────────────────────────────────
export const architectureStages = [
  'Datasets',
  'Signal Preprocessing',
  'Feature Extraction',
  'AI / ML Models',
  'Training',
  'Validation',
  'Testing',
  'Performance Analysis',
  'Final Prediction',
];

// ── ML workflow ──────────────────────────────────────────────────────
export const mlWorkflow = [
  { title: 'Data Preprocessing', detail: 'Cleaning, normalisation, and segmentation of raw signals into model-ready inputs.' },
  { title: 'Feature Engineering', detail: 'Extraction of time-domain, frequency-domain, and morphological descriptors.' },
  { title: 'Model Training', detail: 'Optimisation of model parameters on labelled training data with regularisation.' },
  { title: 'Validation', detail: 'Cross-validation and hyperparameter tuning to ensure generalisation.' },
  { title: 'Testing', detail: 'Evaluation on a held-out test set unseen during training or tuning.' },
  { title: 'Performance Evaluation', detail: 'Comprehensive metrics analysis and error characterisation.' },
];

// ── Models (editable names) ──────────────────────────────────────
export type ModelDef = { id: string; name: string; dataset: string };
export const models: ModelDef[] = [
  { id: 'm1', name: 'SVM — RBF Kernel', dataset: 'DEAP' },
  { id: 'm2', name: 'Random Forest — 200 Trees', dataset: 'DEAP' },
  { id: 'm3', name: 'XGBoost — 300 Estimators', dataset: 'DEAP' },
  { id: 'm4', name: 'CNN — EEG-Net Style', dataset: 'DEAP' },
  { id: 'm5', name: 'LSTM-CNN Hybrid', dataset: 'DEAP' },
];

// ── Comparison metrics ──────────────────────────────────────────────
// Use null for unavailable values — rendered as "—"
export type Metric = number | null;
export type ModelRow = {
  model: string;
  dataset: string;
  accuracy: Metric;
  precision: Metric;
  recall: Metric;
  f1: Metric;
  auc: Metric;
  trainingTime: Metric;
};

export const modelComparisonRows: ModelRow[] = [
  { model: 'SVM', dataset: 'DEAP', accuracy: 75, precision: 0.00, recall: 0.00, f1: 0.00, auc: null, trainingTime: null },
  { model: 'Random Forest', dataset: 'DEAP', accuracy: 87.5, precision: 1.00, recall: 0.50, f1: 0.67, auc: null, trainingTime: null },
  { model: 'XGBoost', dataset: 'DEAP', accuracy: 87.5, precision: 1.00, recall: 0.50, f1: 0.67, auc: null, trainingTime: null },
  { model: 'CNN', dataset: 'DEAP', accuracy: 87.5, precision: 1.00, recall: 0.50, f1: 0.67, auc: null, trainingTime: null },
  { model: 'LSTM-CNN', dataset: 'DEAP', accuracy: 75, precision: 0.71, recall: 0.83, f1: 0.77, auc: null, trainingTime: null },
];

// ── Per-model DEAP results for ResultsDashboard tabs ─────────────────
export type PerModelResult = {
  id: string;
  name: string;
  tagline: string;
  accuracy: Metric;
  precision: Metric;
  recall: Metric;
  f1: Metric;
  confusion: { tp: Metric; fp: Metric; tn: Metric; fn: Metric };
  trainingCurve: { epoch: number; acc: Metric; loss: Metric }[];
  highlights: string[];
};

const flatCurve = (acc: Metric, loss: Metric) =>
  Array.from({ length: 10 }, (_, i) => ({ epoch: i + 1, acc, loss }));

export const deapModelResults: PerModelResult[] = [
  {
    id: 'svm',
    name: 'SVM',
    tagline: 'RBF kernel · C=1.0 · Baseline classifier',
    accuracy: 75, precision: 0.00, recall: 0.00, f1: 0.00,
    confusion: { tn: 6, fp: 0, fn: 2, tp: 0 },
    trainingCurve: flatCurve(75, 0.45),
    highlights: [
      'Simple baseline with mean-per-channel features',
      'Fast training — under 1 second',
      'Under-samples Stress class (0 predicted)',
    ],
  },
  {
    id: 'rf',
    name: 'Random Forest',
    tagline: '200 trees · max_depth=10 · 32 features',
    accuracy: 87.5, precision: 1.00, recall: 0.50, f1: 0.67,
    confusion: { tn: 6, fp: 0, fn: 1, tp: 1 },
    trainingCurve: flatCurve(87.5, 0.21),
    highlights: [
      'Top channel: Ch07 (importance 0.099)',
      'Perfect precision on Stress predictions',
      'Built-in feature ranking for channel analysis',
    ],
  },
  {
    id: 'xgb',
    name: 'XGBoost',
    tagline: '300 estimators · lr=0.05 · 128 bandpower features',
    accuracy: 87.5, precision: 1.00, recall: 0.50, f1: 0.67,
    confusion: { tn: 6, fp: 0, fn: 1, tp: 1 },
    trainingCurve: flatCurve(87.5, 0.15),
    highlights: [
      'Uses 4 bandpowers (θ/α/β/γ) across 32 channels',
      'Gamma band dominates top 6 features',
      'Gradient boosting handles class imbalance well',
    ],
  },
  {
    id: 'cnn',
    name: 'CNN',
    tagline: 'EEG-Net style · Temporal→Spatial→Temporal conv blocks',
    accuracy: 87.5, precision: 1.00, recall: 0.50, f1: 0.67,
    confusion: { tn: 6, fp: 0, fn: 1, tp: 1 },
    trainingCurve: [
      { epoch: 1,  acc: 75.0, loss: 0.74 },
      { epoch: 2,  acc: 75.0, loss: 0.65 },
      { epoch: 3,  acc: 75.0, loss: 0.58 },
      { epoch: 4,  acc: 75.0, loss: 0.49 },
      { epoch: 5,  acc: 75.0, loss: 0.43 },
      { epoch: 6,  acc: 75.0, loss: 0.34 },
      { epoch: 8,  acc: 75.0, loss: 0.22 },
      { epoch: 10, acc: 96.9, loss: 0.16 },
      { epoch: 15, acc: 100,  loss: 0.05 },
      { epoch: 20, acc: 100,  loss: 0.01 },
    ],
    highlights: [
      '100% training accuracy by epoch 15',
      '1×15 temporal → 32×1 spatial → 1×7 temporal conv',
      'Scales to full 32-subject DEAP easily',
    ],
  },
  {
    id: 'lstmcnn',
    name: 'LSTM-CNN',
    tagline: 'Conv1D features per time-step → 64-unit LSTM · 8.4M params',
    accuracy: 75, precision: 0.71, recall: 0.83, f1: 0.77,
    confusion: { tn: 5, fp: 1, fn: 1, tp: 1 },
    trainingCurve: [
      { epoch: 1,  acc: 62.5, loss: 0.68 },
      { epoch: 2,  acc: 62.5, loss: 0.62 },
      { epoch: 3,  acc: 75.0, loss: 0.59 },
      { epoch: 5,  acc: 75.0, loss: 0.53 },
      { epoch: 10, acc: 84.4, loss: 0.39 },
      { epoch: 15, acc: 90.6, loss: 0.29 },
      { epoch: 20, acc: 93.8, loss: 0.22 },
      { epoch: 25, acc: 96.9, loss: 0.17 },
      { epoch: 30, acc: 96.9, loss: 0.14 },
      { epoch: 40, acc: 100,  loss: 0.06 },
    ],
    highlights: [
      '8 time-steps × 64 samples (512 total) sequence modelling',
      '8.4M params — 1D-CNN per step → LSTM (64h) → MLP head',
      'Peaks early at 75% accuracy then overfits past epoch 25',
      'More regularization + cross-subject data would improve',
    ],
  },
];

// ── Highlight metrics for results (overall best across DEAP models) ──
export const highlightMetrics = [
  { label: 'Best Accuracy', value: 87.5 as Metric, suffix: '%' },
  { label: 'Stress Precision', value: 1.00 as Metric, suffix: '' },
  { label: 'Models Evaluated', value: 5 as Metric, suffix: '' },
  { label: 'Top Features', value: 128 as Metric, suffix: '' },
];

// ── Technology stack ──────────────────────────────────────────────
export const technologies = [
  { name: 'Python', icon: 'Code2' },
  { name: 'NumPy', icon: 'Sigma' },
  { name: 'Pandas', icon: 'Table2' },
  { name: 'SciPy', icon: 'AudioWaveform' },
  { name: 'Scikit-learn', icon: 'BrainCircuit' },
  { name: 'TensorFlow / PyTorch', icon: 'Network' },
  { name: 'Matplotlib', icon: 'BarChart3' },
  { name: 'Jupyter', icon: 'NotebookPen' },
];

// ── Timeline ──────────────────────────────────────────────────────
export const timeline = [
  { phase: '01', title: 'Dataset Collection', detail: 'Acquire DEAP benchmark dataset and collect EEG from 15 local participants.' },
  { phase: '02', title: 'Data Understanding', detail: 'Exploratory analysis of signal characteristics and class distributions.' },
  { phase: '03', title: 'Preprocessing', detail: 'Cleaning, artifact removal, and normalisation of raw signals.' },
  { phase: '04', title: 'Signal Analysis', detail: 'Spectral and morphological analysis of the physiological signals.' },
  { phase: '05', title: 'Model Development', detail: 'Design and implementation of ML/DL model architectures.' },
  { phase: '06', title: 'Training', detail: 'Model training with regularisation and early stopping strategies.' },
  { phase: '07', title: 'Evaluation', detail: 'Performance assessment on held-out test data across metrics.' },
  { phase: '08', title: 'Optimisation', detail: 'Hyperparameter tuning and architecture refinement.' },
  { phase: '09', title: 'Final Analysis', detail: 'Consolidation of results and research conclusions.' },
];

// ── Research philosophy ──────────────────────────────────────────────
export const philosophy = [
  { title: 'Data', text: 'Understand the signal before modelling it.' },
  { title: 'Intelligence', text: 'Use AI to identify meaningful patterns.' },
  { title: 'Validation', text: 'Measure performance rather than assuming it.' },
];

// ── Researcher / contact ──────────────────────────────────────────────
export const researcher = {
  name: '[Researcher Name]',
  institution: '[Institution Name]',
  department: '[Department / Programme]',
  email: '[email@institution.edu]',
  github: '[GitHub Username]',
  linkedin: '[LinkedIn Profile]',
  repository: '[Project Repository URL]',
};
