"""Built-in demo knowledge used when a specialty's PDFs cannot be loaded.

The text is taken from the original notebook so the demo behaves the same way.
It is a small, hand-written summary and is NOT a substitute for real guidelines.
"""

from typing import Dict, List, Tuple

# Each entry is (topic, text). The topic becomes Document metadata.

DEMO_DOCUMENTS: Dict[str, List[Tuple[str, str]]] = {
    "diabetes": [
        ("Diagnosis", """            Type 2 Diabetes Mellitus Diagnostic Criteria:
            
            The American Diabetes Association (ADA) diagnostic criteria for Type 2 diabetes mellitus include:
            
            1. Fasting Plasma Glucose (FPG) ≥ 126 mg/dL (7.0 mmol/L)
            2. 2-hour Plasma Glucose ≥ 200 mg/dL (11.1 mmol/L) during OGTT
            3. HbA1c ≥ 6.5% (48 mmol/mol)
            4. Random plasma glucose ≥ 200 mg/dL (11.1 mmol/L) with classic symptoms
            
            Each test should be confirmed on a separate day unless the patient has classic symptoms of hyperglycemia.
            """),
        ("DKA", """            Diabetic Ketoacidosis (DKA) Pathophysiology:
            
            DKA is a serious complication of diabetes characterized by:
            
            1. Insulin deficiency leading to increased lipolysis
            2. Elevated ketone production (β-hydroxybutyrate and acetoacetate)
            3. Metabolic acidosis with anion gap
            4. Severe dehydration and electrolyte imbalances
            
            Clinical presentation includes polyuria, polydipsia, abdominal pain, vomiting, and altered mental status.
            
            Treatment involves IV insulin, fluid resuscitation, and electrolyte replacement.
            """),
        ("Metformin", """            Metformin Therapy Guidelines:
            
            Metformin is the first-line therapy for Type 2 diabetes:
            
            1. Mechanism: Reduces hepatic glucose production, improves insulin sensitivity
            2. Starting dose: 500-850 mg once or twice daily with meals
            3. Maximum dose: 2550 mg daily (divided doses)
            
            Contraindications:
            - eGFR <30 mL/min/1.73m²
            - Acute kidney injury
            - Severe liver disease
            - Heart failure requiring hospitalization
            """),
    ],
    "cancer": [
        ("Breast Cancer", """            Breast Cancer Staging and Treatment:
            
            TNM Staging System for Breast Cancer:
            - T (Tumor size): T1 (<2cm), T2 (2-5cm), T3 (>5cm), T4 (chest wall/skin involvement)
            - N (Lymph nodes): N0 (none), N1 (1-3 axillary), N2 (4-9 axillary), N3 (>9 or other regions)
            - M (Metastasis): M0 (none), M1 (distant metastasis)
            
            Treatment approaches:
            - Surgery: Lumpectomy vs. mastectomy
            - Adjuvant therapy: Chemotherapy, radiation, hormonal therapy
            - Targeted therapy: HER2-positive tumors (trastuzumab)
            - Immunotherapy: Triple-negative breast cancer considerations
            """),
        ("Lung Cancer", """            Lung Cancer Classification and Management:
            
            Two main types:
            1. Non-Small Cell Lung Cancer (NSCLC) - 85% of cases
               - Adenocarcinoma (most common)
               - Squamous cell carcinoma
               - Large cell carcinoma
            
            2. Small Cell Lung Cancer (SCLC) - 15% of cases
               - Limited stage vs. extensive stage
               - More aggressive, better initial response to chemotherapy
            
            Staging: Stage I-IV based on tumor size, lymph node involvement, and metastasis
            Treatment: Surgery, chemotherapy, radiation, targeted therapy, immunotherapy
            """),
        ("Chemotherapy", """            Chemotherapy Principles and Side Effects:
            
            Mechanisms of action:
            - Alkylating agents: DNA cross-linking
            - Antimetabolites: Interfere with DNA synthesis
            - Topoisomerase inhibitors: Prevent DNA unwinding
            - Mitotic inhibitors: Disrupt cell division
            
            Common side effects:
            - Myelosuppression (neutropenia, anemia, thrombocytopenia)
            - Gastrointestinal toxicity (nausea, vomiting, mucositis)
            - Alopecia
            - Peripheral neuropathy
            - Cardiotoxicity (doxorubicin)
            - Pulmonary toxicity (bleomycin)
            """),
    ],
    "mental_health": [
        ("Depression", """            Major Depressive Disorder (MDD) Diagnosis and Treatment:
            
            DSM-5 Criteria for Major Depressive Episode:
            At least 5 symptoms for ≥2 weeks, including depressed mood or anhedonia:
            1. Depressed mood most of the day
            2. Anhedonia (loss of interest/pleasure)
            3. Significant weight change or appetite disturbance
            4. Sleep disturbance (insomnia or hypersomnia)
            5. Psychomotor agitation or retardation
            6. Fatigue or loss of energy
            7. Feelings of worthlessness or excessive guilt
            8. Diminished concentration or indecisiveness
            9. Recurrent thoughts of death or suicidal ideation
            
            Treatment approaches:
            - First-line: SSRIs (sertraline, escitalopram, fluoxetine)
            - Psychotherapy: CBT, IPT, behavioral activation
            - Combination therapy for moderate-severe depression
            """),
        ("Anxiety", """            Anxiety Disorders Classification and Management:
            
            Types of Anxiety Disorders:
            1. Generalized Anxiety Disorder (GAD)
            2. Panic Disorder
            3. Social Anxiety Disorder
            4. Specific Phobias
            5. Agoraphobia
            
            GAD Diagnostic Criteria:
            - Excessive anxiety/worry for ≥6 months
            - Difficult to control worry
            - Associated with ≥3 symptoms: restlessness, fatigue, concentration problems, irritability, muscle tension, sleep disturbance
            
            Treatment:
            - First-line: SSRIs, SNRIs
            - Psychotherapy: CBT, exposure therapy
            - Short-term: Benzodiazepines (avoid long-term use)
            """),
        ("Bipolar", """            Bipolar Disorder Management:
            
            Bipolar I vs. Bipolar II:
            - Bipolar I: At least one manic episode
            - Bipolar II: Hypomanic episodes with major depressive episodes
            
            Manic Episode Criteria:
            - Elevated, expansive, or irritable mood for ≥1 week
            - ≥3 symptoms: Grandiosity, decreased sleep, talkativeness, flight of ideas, distractibility, increased goal-directed activity, risky behavior
            
            Treatment:
            - Mood stabilizers: Lithium, valproate, lamotrigine
            - Atypical antipsychotics: Quetiapine, olanzapine, aripiprazole
            - Psychotherapy: CBT, family therapy, psychoeducation
            - Avoid antidepressant monotherapy (risk of mania induction)
            """),
    ],
    "cardiac": [
        ("MI", """            Acute Myocardial Infarction (STEMI vs NSTEMI):
            
            STEMI (ST-Elevation MI):
            - ECG: ST elevation ≥2mm in precordial leads or ≥1mm in limb leads
            - Treatment: Primary PCI within 90 minutes or fibrinolytic therapy within 30 minutes
            - Antiplatelet therapy: Dual antiplatelet therapy (aspirin + P2Y12 inhibitor)
            - Anticoagulation: Heparin or bivalirudin
            
            NSTEMI (Non-ST-Elevation MI):
            - ECG: ST depression or T-wave inversion
            - Biomarkers: Elevated troponin
            - Risk stratification: TIMI or GRACE score
            - Treatment: Early invasive strategy vs. conservative management
            - Medical therapy: Beta-blockers, ACE inhibitors, statins
            """),
        ("Heart Failure", """            Heart Failure Classification and Management:
            
            NYHA Functional Classification:
            - Class I: No limitation of physical activity
            - Class II: Slight limitation of physical activity
            - Class III: Marked limitation of physical activity
            - Class IV: Unable to carry on physical activity without discomfort
            
            HFrEF (Heart Failure with Reduced Ejection Fraction):
            - EF ≤40%
            - Treatment: ACE inhibitors/ARBs, beta-blockers, aldosterone antagonists
            - Device therapy: ICD, CRT consideration
            
            HFpEF (Heart Failure with Preserved Ejection Fraction):
            - EF ≥50%
            - Treatment: Symptom management, treat comorbidities
            - Limited evidence for mortality benefit
            """),
        ("Hypertension", """            Hypertension Guidelines and Management:
            
            2017 ACC/AHA Blood Pressure Categories:
            - Normal: <120/80 mmHg
            - Elevated: 120-129/<80 mmHg
            - Stage 1: 130-139/80-89 mmHg
            - Stage 2: ≥140/90 mmHg
            - Hypertensive Crisis: >180/120 mmHg
            
            First-line medications:
            - ACE inhibitors or ARBs
            - Thiazide or thiazide-like diuretics
            - Calcium channel blockers
            - Beta-blockers (specific indications)
            
            Target BP: <130/80 mmHg for most patients
            Lifestyle modifications: Diet, exercise, weight loss, sodium restriction
            """),
    ],
}
