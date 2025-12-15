# Alert Trust Metrics

**Canonical Reference** — How to measure and improve Decision Moment quality

---

## Trust Dimensions

### 1. Precision (False Positive Rate)

**Definition:**  
Of all Decision Moments that fired, what percentage were actually meaningful?

**Formula:**
```
Precision = True Positives / (True Positives + False Positives)
```

**Target:** `Precision >= 0.70` (70% of DMs should be meaningful)

**Measurement:**
- Human feedback: Mark DMs as "useful" or "noise"
- Track in `dm_feedback` table:
  ```sql
  CREATE TABLE dm_feedback (
    dm_id TEXT PRIMARY KEY,
    fired_at TEXT,
    symbol TEXT,
    human_rating INTEGER,  -- 1-5 scale
    was_useful BOOLEAN,
    feedback_text TEXT
  )
  ```

---

### 2. Recall (False Negative Rate)

**Definition:**  
Of all meaningful events, what percentage did we catch?

**Formula:**
```
Recall = True Positives / (True Positives + False Negatives)
```

**Target:** `Recall >= 0.60` (60% of meaningful events should trigger DMs)

**Measurement:**
- Post-hoc analysis: Review significant market events
- Check if DM was generated (even if suppressed)
- Track in `event_coverage` table:
  ```sql
  CREATE TABLE event_coverage (
    event_id TEXT PRIMARY KEY,
    event_timestamp TEXT,
    symbol TEXT,
    event_type TEXT,
    dm_generated BOOLEAN,
    dm_triggered BOOLEAN,
    dm_id TEXT
  )
  ```

---

### 3. Latency (Time to Surface)

**Definition:**  
How quickly does the system surface a Decision Moment after the underlying event?

**Formula:**
```
Latency = DM Timestamp - Event Timestamp
```

**Target:** `Latency <= 1 hour` (for 1h window)

**Measurement:**
- Compare `dm.timestamp` with external event timestamps
- Track in `dm_latency` table:
  ```sql
  CREATE TABLE dm_latency (
    dm_id TEXT PRIMARY KEY,
    event_timestamp TEXT,
    dm_timestamp TEXT,
    latency_seconds INTEGER
  )
  ```

---

### 4. Explanation Quality

**Definition:**  
How clear and actionable are Decision Moment explanations?

**Formula:**
```
Explanation Quality = Human Rating (1-5 scale)
```

**Target:** `Average Rating >= 4.0`

**Measurement:**
- Human feedback on `dm.explain()` output
- Track in `dm_feedback.explanation_rating`

---

### 5. Suppression Accuracy

**Definition:**  
Of all suppressed DMs, what percentage were correctly suppressed (i.e., were noise)?

**Formula:**
```
Suppression Accuracy = Correctly Suppressed / Total Suppressed
```

**Target:** `Suppression Accuracy >= 0.90` (90% of suppressions should be correct)

**Measurement:**
- Review suppressed DMs periodically
- Human feedback: "Should this have fired?"
- Track in `suppression_feedback` table

---

## Trust Score Calculation

### Composite Trust Score

```python
def calculate_trust_score(
    precision: float,
    recall: float,
    latency_avg: float,
    explanation_quality: float,
    suppression_accuracy: float
) -> float:
    """Calculate composite trust score (0-1)."""
    
    # Normalize latency (target: 1 hour = 3600 seconds)
    latency_score = max(0, 1 - (latency_avg / 3600))
    
    # Normalize explanation quality (target: 4.0/5.0)
    explanation_score = explanation_quality / 5.0
    
    # Weighted average
    trust_score = (
        precision * 0.30 +           # 30% weight
        recall * 0.25 +              # 25% weight
        latency_score * 0.15 +       # 15% weight
        explanation_score * 0.15 +   # 15% weight
        suppression_accuracy * 0.15  # 15% weight
    )
    
    return min(1.0, max(0.0, trust_score))
```

**Target:** `Trust Score >= 0.75`

---

## Metrics Dashboard Schema

```sql
CREATE TABLE trust_metrics (
  date TEXT PRIMARY KEY,
  
  -- Precision
  total_dms_fired INTEGER,
  true_positives INTEGER,
  false_positives INTEGER,
  precision REAL,
  
  -- Recall
  total_meaningful_events INTEGER,
  false_negatives INTEGER,
  recall REAL,
  
  -- Latency
  avg_latency_seconds REAL,
  p50_latency_seconds REAL,
  p95_latency_seconds REAL,
  
  -- Explanation Quality
  avg_explanation_rating REAL,
  explanation_feedback_count INTEGER,
  
  -- Suppression Accuracy
  total_suppressed INTEGER,
  correctly_suppressed INTEGER,
  suppression_accuracy REAL,
  
  -- Composite
  trust_score REAL
);
```

---

## Trust Improvement Strategies

### Strategy 1: Tune Policy Thresholds

**If Precision Too Low (too many false positives):**
- Increase `min_signals` (require more signals)
- Increase `min_velocity_multiplier` (higher threshold)
- Increase `cooldown_seconds` (longer cooldown)
- Set `allow_recurring_patterns=False` (block recurring)

**If Recall Too Low (too many false negatives):**
- Decrease `min_signals` (allow fewer signals)
- Decrease `min_velocity_multiplier` (lower threshold)
- Decrease `cooldown_seconds` (shorter cooldown)
- Set `require_alignment=False` (alignment optional)

---

### Strategy 2: Improve Signal Quality

**If Explanation Quality Too Low:**
- Add more context to `SignalEvidence.note`
- Include historical comparisons in `interpretation_summary`
- Add `uncertainty` field with specific risks
- Include `interpretation_exclusion` (what it's NOT)

---

### Strategy 3: Reduce Latency

**If Latency Too High:**
- Reduce API cache TTL (fresher data)
- Use shorter time windows (1h instead of 4h)
- Parallelize API calls
- Optimize database queries

---

### Strategy 4: Improve Suppression Accuracy

**If Suppression Accuracy Too Low:**
- Review suppressed DMs that should have fired
- Adjust policy thresholds based on feedback
- Add new policy rules for edge cases
- Improve signal quality (better signals = better suppression)

---

## Trust Monitoring Queries

### Daily Trust Report

```sql
SELECT 
  date,
  trust_score,
  precision,
  recall,
  avg_latency_seconds / 3600.0 as avg_latency_hours,
  avg_explanation_rating,
  suppression_accuracy
FROM trust_metrics
WHERE date >= date('now', '-7 days')
ORDER BY date DESC;
```

### Precision Trend

```sql
SELECT 
  date,
  precision,
  total_dms_fired,
  false_positives
FROM trust_metrics
WHERE date >= date('now', '-30 days')
ORDER BY date DESC;
```

### Suppression Analysis

```sql
SELECT 
  symbol,
  COUNT(*) as suppressed_count,
  AVG(CASE WHEN correctly_suppressed THEN 1.0 ELSE 0.0 END) as suppression_accuracy
FROM suppression_feedback
WHERE date >= date('now', '-7 days')
GROUP BY symbol
ORDER BY suppressed_count DESC;
```

---

## Trust Targets (Canonical)

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Precision | ≥ 0.70 | < 0.50 |
| Recall | ≥ 0.60 | < 0.40 |
| Latency | ≤ 1 hour | > 4 hours |
| Explanation Quality | ≥ 4.0/5.0 | < 3.0/5.0 |
| Suppression Accuracy | ≥ 0.90 | < 0.70 |
| **Trust Score** | **≥ 0.75** | **< 0.60** |

---

## Trust Score Interpretation

### Trust Score ≥ 0.75 (Green)

✅ System is trustworthy  
✅ DMs are reliable  
✅ Continue current policy

---

### Trust Score 0.60 - 0.74 (Yellow)

⚠️ System needs tuning  
⚠️ Review policy thresholds  
⚠️ Improve signal quality

---

### Trust Score < 0.60 (Red)

🔴 System not trustworthy  
🔴 Major policy revision needed  
🔴 Review all metrics

---

## Trust Feedback Loop

```
1. Fire Decision Moment
   ↓
2. Human evaluates (useful/noise)
   ↓
3. Record feedback
   ↓
4. Calculate trust metrics
   ↓
5. Tune policy if needed
   ↓
6. Repeat
```

---

*End of Alert Trust Metrics*
