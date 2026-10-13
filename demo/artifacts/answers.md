## SYN-01

Snapshot: 1. Question: How many therapy sessions, treatment days, and minutes did Casey Demo receive from March 1 through March 14, 2027?

Review window: 2027-03-01 through 2027-03-14, inclusive.

Eligible sessions: **2**. Distinct therapy days: **2**. Therapy minutes: **250** (**4.167 hours**, rounded to 3 decimals).

Monday-Sunday weekly calculations use the review-range contributions below. Thresholds are the documented goals; partial weeks are not silently prorated.

| Calendar week | Reviewed dates | Days | Minutes | Hours | Goal | Decision | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2027-03-01 to 2027-03-07 | 2027-03-01 to 2027-03-07 | 1 | 120 | 2.000 | 1 days and 150 minutes | not_met | [1], [2], [5], [6], [7], [8], [9] |
| 2027-03-08 to 2027-03-14 | 2027-03-08 to 2027-03-14 | 1 | 130 | 2.167 | 1 days and 150 minutes | not_met | [3], [4], [5], [6], [7], [8], [9] |

Calculation ledger:

| Date | Encounter | Service | Included | Contact minutes | Reason | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 2027-03-01 | SYN-CASEY-E1 | individual | included | 120 | Eligible attended patient therapy under the effective plan. | [1], [2] |
| 2027-03-08 | SYN-CASEY-E2 | individual | included | 130 | Eligible attended patient therapy under the effective plan. | [3], [4] |

Reconciliation decisions:

- SYN-CASEY-E1, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [1], [2]
- SYN-CASEY-E1, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [1], [2]
- SYN-CASEY-E2, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [3], [4]
- SYN-CASEY-E2, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [3], [4]


Source passages:

[1] SYN-CASEY-W1, SYN-CASEY-W1.txt, lines 6-11: Final patient-contact note for SYN-CASEY. Encounter ID: SYN-CASEY-E1. Service date: 2027-03-01. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 120 minutes. This is an independently signed final note, not a copy or a correction.
[2] SYN-CASEY-W1, SYN-CASEY-W1.txt, lines 10-10: Patient-present individual psychotherapy duration: 120 minutes.
[3] SYN-CASEY-W2, SYN-CASEY-W2.txt, lines 6-11: Final patient-contact note for SYN-CASEY. Encounter ID: SYN-CASEY-E2. Service date: 2027-03-08. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 130 minutes. This is an independently signed final note, not a copy or a correction.
[4] SYN-CASEY-W2, SYN-CASEY-W2.txt, lines 10-10: Patient-present individual psychotherapy duration: 130 minutes.
[5] SYN-CASEY-PLAN, SYN-CASEY-PLAN.txt, lines 6-12: Final treatment plan for SYN-CASEY. Plan effective start: 2027-03-01. Plan effective end: 2027-03-14. Minimum distinct treatment days: 1 day. Minimum patient-contact time: 150 minutes. Requirements apply to each Monday-Sunday calendar week. Only individual psychotherapy with the patient present counts toward these goals.
[6] SYN-CASEY-PLAN, SYN-CASEY-PLAN.txt, lines 7-7: Plan effective start: 2027-03-01.
[7] SYN-CASEY-PLAN, SYN-CASEY-PLAN.txt, lines 8-8: Plan effective end: 2027-03-14.
[8] SYN-CASEY-PLAN, SYN-CASEY-PLAN.txt, lines 9-9: Minimum distinct treatment days: 1 day.
[9] SYN-CASEY-PLAN, SYN-CASEY-PLAN.txt, lines 10-10: Minimum patient-contact time: 150 minutes.

## SYN-02

Snapshot: 1. Question: Which patients had two consecutive weeks below their documented treatment requirements from March 1 through March 28, 2027?

Review window: 2027-03-01 through 2027-03-28. Membership is evaluated within consistent interpretations across adjacent calendar weeks.

| Patient | Membership | Reason | Sources |
| --- | --- | --- | --- |
| Alex Demo | excluded | No consistent interpretation has 2 consecutive below-goal weeks. | [1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12], [13], [14], [15], [16], [17], [18], [19], [20] |
| Casey Demo | confirmed | Every consistent interpretation has 2 consecutive below-goal weeks. | [21], [22], [23], [24], [25], [26], [27], [28], [29] |

Witness week 2027-03-01: 1 days, 120 minutes, not_met; encounters SYN-CASEY-E1.

Witness week 2027-03-08: 1 days, 130 minutes, not_met; encounters SYN-CASEY-E2.
| Morgan Demo | possible | A consistent source interpretation establishes 2 consecutive below-goal weeks. | [30], [31], [32], [33], [34], [35], [36], [37], [38], [39], [40], [41], [42] |

Witness week 2027-03-01: 1 days, 130 minutes, not_met; encounters SYN-MORGAN-E1.

Witness week 2027-03-08: 1 days, 130 minutes, not_met; encounters SYN-MORGAN-E2.

Unresolved conclusions and limitations:

- Morgan Demo: A consistent source interpretation establishes 2 consecutive below-goal weeks.

Additional evidence needed:

- patient synthetic review clinic::SYN-MORGAN, SYN-MORGAN-E1, 2027-03-01 through 2027-03-28, duration: Supported records disagree on actual patient-contact duration: 130 or 170 minutes. Obtain an explicit duration correction scoped to patient synthetic review clinic::SYN-MORGAN, encounter SYN-MORGAN-E1, 2027-03-01, identifying which earlier assertion it replaces, or the actual patient-contact start/end times and break record for that encounter. [30], [31], [32], [33]
- patient synthetic review clinic::SYN-MORGAN, SYN-MORGAN-E2, 2027-03-01 through 2027-03-28, duration: Supported records disagree on actual patient-contact duration: 130 or 170 minutes. Obtain an explicit duration correction scoped to patient synthetic review clinic::SYN-MORGAN, encounter SYN-MORGAN-E2, 2027-03-08, identifying which earlier assertion it replaces, or the actual patient-contact start/end times and break record for that encounter. [39], [40], [41], [42]

Source passages:

[1] SYN-ALEX-W1, SYN-ALEX-W1.txt, lines 6-11: Final patient-contact note for SYN-ALEX. Encounter ID: SYN-ALEX-E1. Service date: 2027-03-01. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 100 minutes. This is an independently signed final note, not a copy or a correction.
[2] SYN-ALEX-W1, SYN-ALEX-W1.txt, lines 10-10: Patient-present individual psychotherapy duration: 100 minutes.
[3] SYN-ALEX-PLAN-OLD, SYN-ALEX-PLAN-OLD.txt, lines 6-12: Final treatment plan for SYN-ALEX. Plan effective start: 2027-03-01. Plan effective end: 2027-03-14. Minimum distinct treatment days: 1 day. Minimum patient-contact time: 100 minutes. Requirements apply to each Monday-Sunday calendar week. Only individual psychotherapy with the patient present counts toward these goals.
[4] SYN-ALEX-PLAN-OLD, SYN-ALEX-PLAN-OLD.txt, lines 7-7: Plan effective start: 2027-03-01.
[5] SYN-ALEX-PLAN-OLD, SYN-ALEX-PLAN-OLD.txt, lines 8-8: Plan effective end: 2027-03-14.
[6] SYN-ALEX-PLAN-OLD, SYN-ALEX-PLAN-OLD.txt, lines 9-9: Minimum distinct treatment days: 1 day.
[7] SYN-ALEX-PLAN-OLD, SYN-ALEX-PLAN-OLD.txt, lines 10-10: Minimum patient-contact time: 100 minutes.
[8] SYN-ALEX-W2, SYN-ALEX-W2.txt, lines 6-11: Final patient-contact note for SYN-ALEX. Encounter ID: SYN-ALEX-E2. Service date: 2027-03-08. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 110 minutes. This is an independently signed final note, not a copy or a correction.
[9] SYN-ALEX-W2, SYN-ALEX-W2.txt, lines 10-10: Patient-present individual psychotherapy duration: 110 minutes.
[10] SYN-ALEX-W3, SYN-ALEX-W3.txt, lines 6-11: Final patient-contact note for SYN-ALEX. Encounter ID: SYN-ALEX-E3. Service date: 2027-03-15. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 120 minutes. This is an independently signed final note, not a copy or a correction.
[11] SYN-ALEX-W3, SYN-ALEX-W3.txt, lines 10-10: Patient-present individual psychotherapy duration: 120 minutes.
[12] SYN-ALEX-PLAN-NEW, SYN-ALEX-PLAN-NEW.txt, lines 6-12: Final treatment plan for SYN-ALEX. Plan effective start: 2027-03-15. Plan effective end: 2027-03-28. Minimum distinct treatment days: 2 days. Minimum patient-contact time: 150 minutes. Requirements apply to each Monday-Sunday calendar week. Only individual psychotherapy with the patient present counts toward these goals.
[13] SYN-ALEX-PLAN-NEW, SYN-ALEX-PLAN-NEW.txt, lines 7-7: Plan effective start: 2027-03-15.
[14] SYN-ALEX-PLAN-NEW, SYN-ALEX-PLAN-NEW.txt, lines 8-8: Plan effective end: 2027-03-28.
[15] SYN-ALEX-PLAN-NEW, SYN-ALEX-PLAN-NEW.txt, lines 9-9: Minimum distinct treatment days: 2 days.
[16] SYN-ALEX-PLAN-NEW, SYN-ALEX-PLAN-NEW.txt, lines 10-10: Minimum patient-contact time: 150 minutes.
[17] SYN-ALEX-W4-A, SYN-ALEX-W4-A.txt, lines 6-11: Final patient-contact note for SYN-ALEX. Encounter ID: SYN-ALEX-E4. Service date: 2027-03-22. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 100 minutes. This is an independently signed final note, not a copy or a correction.
[18] SYN-ALEX-W4-A, SYN-ALEX-W4-A.txt, lines 10-10: Patient-present individual psychotherapy duration: 100 minutes.
[19] SYN-ALEX-W4-B, SYN-ALEX-W4-B.txt, lines 6-11: Final patient-contact note for SYN-ALEX. Encounter ID: SYN-ALEX-E5. Service date: 2027-03-23. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 60 minutes. This is an independently signed final note, not a copy or a correction.
[20] SYN-ALEX-W4-B, SYN-ALEX-W4-B.txt, lines 10-10: Patient-present individual psychotherapy duration: 60 minutes.
[21] SYN-CASEY-W1, SYN-CASEY-W1.txt, lines 6-11: Final patient-contact note for SYN-CASEY. Encounter ID: SYN-CASEY-E1. Service date: 2027-03-01. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 120 minutes. This is an independently signed final note, not a copy or a correction.
[22] SYN-CASEY-W1, SYN-CASEY-W1.txt, lines 10-10: Patient-present individual psychotherapy duration: 120 minutes.
[23] SYN-CASEY-PLAN, SYN-CASEY-PLAN.txt, lines 6-12: Final treatment plan for SYN-CASEY. Plan effective start: 2027-03-01. Plan effective end: 2027-03-14. Minimum distinct treatment days: 1 day. Minimum patient-contact time: 150 minutes. Requirements apply to each Monday-Sunday calendar week. Only individual psychotherapy with the patient present counts toward these goals.
[24] SYN-CASEY-PLAN, SYN-CASEY-PLAN.txt, lines 7-7: Plan effective start: 2027-03-01.
[25] SYN-CASEY-PLAN, SYN-CASEY-PLAN.txt, lines 8-8: Plan effective end: 2027-03-14.
[26] SYN-CASEY-PLAN, SYN-CASEY-PLAN.txt, lines 9-9: Minimum distinct treatment days: 1 day.
[27] SYN-CASEY-PLAN, SYN-CASEY-PLAN.txt, lines 10-10: Minimum patient-contact time: 150 minutes.
[28] SYN-CASEY-W2, SYN-CASEY-W2.txt, lines 6-11: Final patient-contact note for SYN-CASEY. Encounter ID: SYN-CASEY-E2. Service date: 2027-03-08. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 130 minutes. This is an independently signed final note, not a copy or a correction.
[29] SYN-CASEY-W2, SYN-CASEY-W2.txt, lines 10-10: Patient-present individual psychotherapy duration: 130 minutes.
[30] SYN-MORGAN-W1-A, SYN-MORGAN-W1-A.txt, lines 6-11: Final patient-contact note for SYN-MORGAN. Encounter ID: SYN-MORGAN-E1. Service date: 2027-03-01. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 130 minutes. This is an independently signed final note, not a copy or a correction.
[31] SYN-MORGAN-W1-A, SYN-MORGAN-W1-A.txt, lines 10-10: Patient-present individual psychotherapy duration: 130 minutes.
[32] SYN-MORGAN-W1-B, SYN-MORGAN-W1-B.txt, lines 6-11: Final patient-contact note for SYN-MORGAN. Encounter ID: SYN-MORGAN-E1. Service date: 2027-03-01. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 170 minutes. This is an independently signed final note, not a copy or a correction.
[33] SYN-MORGAN-W1-B, SYN-MORGAN-W1-B.txt, lines 10-10: Patient-present individual psychotherapy duration: 170 minutes.
[34] SYN-MORGAN-PLAN, SYN-MORGAN-PLAN.txt, lines 6-12: Final treatment plan for SYN-MORGAN. Plan effective start: 2027-03-01. Plan effective end: 2027-03-14. Minimum distinct treatment days: 1 day. Minimum patient-contact time: 150 minutes. Requirements apply to each Monday-Sunday calendar week. Only individual psychotherapy with the patient present counts toward these goals.
[35] SYN-MORGAN-PLAN, SYN-MORGAN-PLAN.txt, lines 7-7: Plan effective start: 2027-03-01.
[36] SYN-MORGAN-PLAN, SYN-MORGAN-PLAN.txt, lines 8-8: Plan effective end: 2027-03-14.
[37] SYN-MORGAN-PLAN, SYN-MORGAN-PLAN.txt, lines 9-9: Minimum distinct treatment days: 1 day.
[38] SYN-MORGAN-PLAN, SYN-MORGAN-PLAN.txt, lines 10-10: Minimum patient-contact time: 150 minutes.
[39] SYN-MORGAN-W2-A, SYN-MORGAN-W2-A.txt, lines 6-11: Final patient-contact note for SYN-MORGAN. Encounter ID: SYN-MORGAN-E2. Service date: 2027-03-08. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 130 minutes. This is an independently signed final note, not a copy or a correction.
[40] SYN-MORGAN-W2-A, SYN-MORGAN-W2-A.txt, lines 10-10: Patient-present individual psychotherapy duration: 130 minutes.
[41] SYN-MORGAN-W2-B, SYN-MORGAN-W2-B.txt, lines 6-11: Final patient-contact note for SYN-MORGAN. Encounter ID: SYN-MORGAN-E2. Service date: 2027-03-08. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 170 minutes. This is an independently signed final note, not a copy or a correction.
[42] SYN-MORGAN-W2-B, SYN-MORGAN-W2-B.txt, lines 10-10: Patient-present individual psychotherapy duration: 170 minutes.

## SYN-03

Snapshot: 1. Question: Compare Alex Demo's sessions, treatment days, total minutes, and weekly goal attainment before and after the March 15, 2027 treatment plan change, using March 1 through March 28, 2027.

Plan-change date: 2027-03-15. Compare explicit windows and service mix; window lengths may differ. Separate period alternatives must not be combined as independent scenarios.

Review window: 2027-03-01 through 2027-03-14, inclusive.

Eligible sessions: **2**. Distinct therapy days: **2**. Therapy minutes: **210** (**3.500 hours**, rounded to 3 decimals).

Monday-Sunday weekly calculations use the review-range contributions below. Thresholds are the documented goals; partial weeks are not silently prorated.

| Calendar week | Reviewed dates | Days | Minutes | Hours | Goal | Decision | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2027-03-01 to 2027-03-07 | 2027-03-01 to 2027-03-07 | 1 | 100 | 1.667 | 1 days and 100 minutes | met | [11], [12], [1], [2], [3], [4], [5] |
| 2027-03-08 to 2027-03-14 | 2027-03-08 to 2027-03-14 | 1 | 110 | 1.833 | 1 days and 100 minutes | met | [13], [14], [1], [2], [3], [4], [5] |

Calculation ledger:

| Date | Encounter | Service | Included | Contact minutes | Reason | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 2027-03-01 | SYN-ALEX-E1 | individual | included | 100 | Eligible attended patient therapy under the effective plan. | [11], [12] |
| 2027-03-08 | SYN-ALEX-E2 | individual | included | 110 | Eligible attended patient therapy under the effective plan. | [13], [14] |

Review window: 2027-03-15 through 2027-03-28, inclusive.

Eligible sessions: **3**. Distinct therapy days: **3**. Therapy minutes: **280** (**4.667 hours**, rounded to 3 decimals).

Monday-Sunday weekly calculations use the review-range contributions below. Thresholds are the documented goals; partial weeks are not silently prorated.

| Calendar week | Reviewed dates | Days | Minutes | Hours | Goal | Decision | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2027-03-15 to 2027-03-21 | 2027-03-15 to 2027-03-21 | 1 | 120 | 2.000 | 2 days and 150 minutes | not_met | [15], [16], [6], [7], [8], [9], [10] |
| 2027-03-22 to 2027-03-28 | 2027-03-22 to 2027-03-28 | 2 | 160 | 2.667 | 2 days and 150 minutes | met | [17], [18], [19], [20], [6], [7], [8], [9], [10] |

Calculation ledger:

| Date | Encounter | Service | Included | Contact minutes | Reason | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 2027-03-15 | SYN-ALEX-E3 | individual | included | 120 | Eligible attended patient therapy under the effective plan. | [15], [16] |
| 2027-03-22 | SYN-ALEX-E4 | individual | included | 100 | Eligible attended patient therapy under the effective plan. | [17], [18] |
| 2027-03-23 | SYN-ALEX-E5 | individual | included | 60 | Eligible attended patient therapy under the effective plan. | [19], [20] |

Reconciliation decisions:

- SYN-ALEX-E1, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [11], [12]
- SYN-ALEX-E1, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [11], [12]
- SYN-ALEX-E2, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [13], [14]
- SYN-ALEX-E2, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [13], [14]
- SYN-ALEX-E3, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [15], [16]
- SYN-ALEX-E3, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [15], [16]
- SYN-ALEX-E4, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [17], [18]
- SYN-ALEX-E4, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [17], [18]
- SYN-ALEX-E5, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [19], [20]
- SYN-ALEX-E5, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [19], [20]


Source passages:

[1] SYN-ALEX-PLAN-OLD, SYN-ALEX-PLAN-OLD.txt, lines 6-12: Final treatment plan for SYN-ALEX. Plan effective start: 2027-03-01. Plan effective end: 2027-03-14. Minimum distinct treatment days: 1 day. Minimum patient-contact time: 100 minutes. Requirements apply to each Monday-Sunday calendar week. Only individual psychotherapy with the patient present counts toward these goals.
[2] SYN-ALEX-PLAN-OLD, SYN-ALEX-PLAN-OLD.txt, lines 7-7: Plan effective start: 2027-03-01.
[3] SYN-ALEX-PLAN-OLD, SYN-ALEX-PLAN-OLD.txt, lines 8-8: Plan effective end: 2027-03-14.
[4] SYN-ALEX-PLAN-OLD, SYN-ALEX-PLAN-OLD.txt, lines 9-9: Minimum distinct treatment days: 1 day.
[5] SYN-ALEX-PLAN-OLD, SYN-ALEX-PLAN-OLD.txt, lines 10-10: Minimum patient-contact time: 100 minutes.
[6] SYN-ALEX-PLAN-NEW, SYN-ALEX-PLAN-NEW.txt, lines 6-12: Final treatment plan for SYN-ALEX. Plan effective start: 2027-03-15. Plan effective end: 2027-03-28. Minimum distinct treatment days: 2 days. Minimum patient-contact time: 150 minutes. Requirements apply to each Monday-Sunday calendar week. Only individual psychotherapy with the patient present counts toward these goals.
[7] SYN-ALEX-PLAN-NEW, SYN-ALEX-PLAN-NEW.txt, lines 7-7: Plan effective start: 2027-03-15.
[8] SYN-ALEX-PLAN-NEW, SYN-ALEX-PLAN-NEW.txt, lines 8-8: Plan effective end: 2027-03-28.
[9] SYN-ALEX-PLAN-NEW, SYN-ALEX-PLAN-NEW.txt, lines 9-9: Minimum distinct treatment days: 2 days.
[10] SYN-ALEX-PLAN-NEW, SYN-ALEX-PLAN-NEW.txt, lines 10-10: Minimum patient-contact time: 150 minutes.
[11] SYN-ALEX-W1, SYN-ALEX-W1.txt, lines 6-11: Final patient-contact note for SYN-ALEX. Encounter ID: SYN-ALEX-E1. Service date: 2027-03-01. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 100 minutes. This is an independently signed final note, not a copy or a correction.
[12] SYN-ALEX-W1, SYN-ALEX-W1.txt, lines 10-10: Patient-present individual psychotherapy duration: 100 minutes.
[13] SYN-ALEX-W2, SYN-ALEX-W2.txt, lines 6-11: Final patient-contact note for SYN-ALEX. Encounter ID: SYN-ALEX-E2. Service date: 2027-03-08. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 110 minutes. This is an independently signed final note, not a copy or a correction.
[14] SYN-ALEX-W2, SYN-ALEX-W2.txt, lines 10-10: Patient-present individual psychotherapy duration: 110 minutes.
[15] SYN-ALEX-W3, SYN-ALEX-W3.txt, lines 6-11: Final patient-contact note for SYN-ALEX. Encounter ID: SYN-ALEX-E3. Service date: 2027-03-15. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 120 minutes. This is an independently signed final note, not a copy or a correction.
[16] SYN-ALEX-W3, SYN-ALEX-W3.txt, lines 10-10: Patient-present individual psychotherapy duration: 120 minutes.
[17] SYN-ALEX-W4-A, SYN-ALEX-W4-A.txt, lines 6-11: Final patient-contact note for SYN-ALEX. Encounter ID: SYN-ALEX-E4. Service date: 2027-03-22. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 100 minutes. This is an independently signed final note, not a copy or a correction.
[18] SYN-ALEX-W4-A, SYN-ALEX-W4-A.txt, lines 10-10: Patient-present individual psychotherapy duration: 100 minutes.
[19] SYN-ALEX-W4-B, SYN-ALEX-W4-B.txt, lines 6-11: Final patient-contact note for SYN-ALEX. Encounter ID: SYN-ALEX-E5. Service date: 2027-03-23. Attendance: attended. Patient present: yes. Patient-present individual psychotherapy duration: 60 minutes. This is an independently signed final note, not a copy or a correction.
[20] SYN-ALEX-W4-B, SYN-ALEX-W4-B.txt, lines 10-10: Patient-present individual psychotherapy duration: 60 minutes.
