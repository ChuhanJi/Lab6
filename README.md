# TECHIN 515 – Lab 6: Speaker Identification on the Edge

You will build a speaker identification system that runs on a microcontroller using an I2S MEMS microphone. The system must distinguish between enrolled speakers and reject unknown ones. You will then evaluate your system's trade-offs through systematic testing and ablation studies.

> **Important**: Voice is **identity data**. This lab includes mandatory ethics and data-handling requirements. Treat all recordings as sensitive.

---

## Learning Objectives

By completing this lab you will:

1. Build an **end-to-end embedded ML pipeline from scratch**: data collection → feature extraction → model training → on-device deployment → decision logic.
2. Design and justify a **repeatable test protocol** with quantitative evidence.
3. Perform **ablation studies** to support design decisions with data, not intuition.
4. Analyze key edge trade-offs, e.g., accuracy vs. latency, latency vs. battery life, thresholding vs. error rates, model size vs. memory constraints, privacy risk vs. utility.
5. Understand risks of ML models by performing red teaming

---

## Hardware Requirements

- **ESP32**: This will be your MCU for this lab
- **ICS-43432 I2S MEMS Microphone** — [datasheet (PDF)](https://product.tdk.com/system/files/dam/doc/product/sw_piezo/mic/mems-mic/data_sheet/ics-43432-data-sheet-v1.3.pdf)
- **Breadboard + jumper wires**
- **LiPo battery (3.7V, 500 mAh+)**

Use the ICS-43432 datasheet to determine the correct wiring to your ESP32.

---

## Software Requirements

- **Arduino IDE or PlatformIO** with ESP32 board package
- **Python 3.11+** — choose your own libraries for data collection, parsing, and analysis
- **Edge Impulse Studio** account ([studio.edgeimpulse.com](https://studio.edgeimpulse.com))

---

## Ethics + Data Governance (Mandatory)

### 1) Consent

Voice is biometric identity data. You must:

1. Ask each participant for explicit consent to record their voice for this lab.
2. Allow an easy opt-out with no penalty.
3. Respect withdrawal: if someone withdraws, delete their data and do not use it.

Prepare a consent form (you can search for templates online) and have your participants sign it before data collection. All your signed consent forms must be submitted.

**Before signing the form, please carefully review it.**

### 2) Data minimization rules

1. Use **pseudonymous IDs** only: `S1`, `S2`, etc. No names, no student IDs.
2. Use a **neutral passphrase** (provided below) — do not record personal information.
3. Do not upload raw audio to any public repository or public dataset.
4. Depending on data management policy in your consent form, keep raw data local to your machine or in private course storage only, or remove all data after lab completion.

### 3) Passphrase

All recordings must use the same phrase:

> "AI runs on edge"

Speak the passphrase at natural pace. Configure your audio capture window to accommodate the full utterance.


### 4) Ethics questions

Answer these in your report:

1. What are two realistic misuse scenarios for speaker identification?
2. What data-handling policy would you recommend for a real product (retention, access control, deletion)?
3. If a user revokes consent after model training, is deleting their audio sufficient? What about the trained model weights?
4. If every speaker says a unique sentence and the inference performance is good, can you safely claim the model learned speakers' voice characteristics? Justify

---

## What You Must Build

Your final system must:

1. **Record** a short audio window from the microphone.
2. **Classify** the speaker as one of K enrolled speakers or "Unknown."
3. **Handle unknowns** — reject low-confidence predictions.
4. **Indicate** the result via reasonable output, e.g., LED, some actuator. Serial output via USB cable does NOT count.
5. **Log results** in a structured, machine-readable format that you design. Include at minimum: predicted label, confidence, and timing metrics (capture time, inference time, total time). Results are not necessarily logged on the edge.
6. **Design and implement battery-aware operation.** Briefly explain how your design may prolong battery life.

---

## Part 1 — Data Collection

Collect a labeled audio dataset for training and evaluation. Before you start, think through:

- How many samples per speaker do you need for reliable training and evaluation? Justify your choice.
- What diversity do your samples need (e.g., different sessions, environments, microphone distances)?
- How will you handle the "Unknown" class — who speaks for it, and how many samples?

**Minimum requirements:** At least 5 enrolled speakers, recorded across 10 sessions per speaker, with a held-out session for testing. That is, you should have 6 classes in total.

**Note**: Collecting the minimum data as instructed above may lead to very poor model performance, and make the last red teaming section challenging.

---

## Part 2 — Model Pipeline

Train a speaker identification model using Edge Impulse (or another framework if you prefer, as long as you can deploy to ESP32).

Document all your parameters choices and design decisions. Justify your choices by evaluations.
Systematically vary at least 2 design choices, one at a time, while holding everything else constant. For example, you might hold the classifier fixed and vary the feature extraction method, then hold features fixed and vary the classifier architecture. For each variation, record accuracy, model size (KB), and estimated inference time. Justify your final model selection with evidence.

---

## Part 3 — On-Device Deployment and Performance Monitoring

Deploy your trained model on edge to perform battery-aware speaker identification. Ensure results are logged.

---

## Part 4 — Evaluation

Design an evaluation protocol to convey the effectiveness of your build.

Before running evaluations, answer:

- What metric to use? Justify.
- How many trials do you need to have confidence in your results?
- Do you need new speakers, who are not involved in data collection, for testing?
  
Run your evaluations, parse your logs, and analyze the results. Write your own analysis scripts or notebook to visualize the evaluation results.

---

## Model Stealing

Now you have finished the pipleline of speaker identificaiton. 
In what follows, you will perform red teaming to assess your pipeline against adversarial attacks.
We first consider model stealing attack that aims to extract your model without going through all data collection, parameter tuning steps.

1. Build your own query set.
2. Query your own deployed model via audio playback, collect (audio → label, confidence) pairs.
3. Train a surrogate classifier on those pairs. Justify your choice of the model architecture.
4. Measure agreement rate with the victim on a held-out query set, as a function of query budget (e.g., 50, 200, 1000 queries).
5. Save your surrogate model as the final stolen model.

---

## Bonus -- Side Channel Attack (Power Analysis)

In this part, your goal is to analyze the power trace of your device and use the power trace to disclose the speaker identity at inference time.

Before you start, think about 
1. how many power traces should be measured per class. 
2. how to handle noises in measurements

3. Use the provided [PPK II](https://docs.nordicsemi.com/bundle/ug_ppk2/page/UG/ppk/PPK_user_guide_Intro.html) to measure the power trace of your deployed speaker identification model at inference time. Document your power trace and the groudtruth class. 
4. Propose a method to classify power traces to speaker identities.
5. Test your method in step 2 on a held-out dataset.
6. Report your speaker identity disclosure performance.

Note: Depending on your Wi-Fi state, model architecture chosen when classifying speakers, the measured power may vary.

---

## Submission Requirements

Submit all code, log results, and all artifacts generated in this lab to Github classroom on the main branch. Make sure your results are **reproducible**.
You should decide whether raw audio data will be included in the private Github repo or not based on your data policy.
Your README should include answers to all questions.

**Include a demo video (3min max) to show successful identification of 2 speakers and 1 unknown speaker.**
Video can be submitted on Canvas as a comment to your submission.