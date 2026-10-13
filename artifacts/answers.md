## DEV-01

Snapshot: 1. Question: For January 5–30, 2026, how many therapy sessions did Rowan attend, by service type and in total, and on how many distinct days? Provide a reviewable abstraction with source support and explain records that could lead to duplicate or ineligible counts.

Review window: 2026-01-05 through 2026-01-30, inclusive.

Eligible sessions: **12**. Distinct therapy days: **11**.

| Service | Eligible sessions |
| --- | --- |
| collateral | 0 |
| coordination | 0 |
| family | 2 |
| group | 5 |
| individual | 5 |
| medication | 0 |

Monday-Sunday weekly calculations use the review-range contributions below. Thresholds are the documented goals; partial weeks are not silently prorated.

| Calendar week | Reviewed dates | Days | Minutes | Hours | Goal | Decision | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-01-05 to 2026-01-11 | 2026-01-05 to 2026-01-11 | 3 | 140 | 2.333 | 3 days and 150 minutes | not_met | [6], [7], [8], [9], [10], [11], [12], [13], [14], [15], [16], [17], [18], [19], [102], [103], [104], [105], [20], [21], [22], [23], [24], [25], [26], [27], [142], [143], [144], [145], [146] |
| 2026-01-12 to 2026-01-18 | 2026-01-12 to 2026-01-18 | 2 | 120 | 2.000 | 3 days and 150 minutes | not_met | [28], [29], [30], [31], [32], [33], [34], [35], [106], [107], [108], [109], [110], [36], [37], [38], [111], [112], [113], [114], [115], [116], [117], [118], [119], [120], [121], [142], [143], [144], [145], [146] |
| 2026-01-19 to 2026-01-25 | 2026-01-19 to 2026-01-25 | 3 | 180 | 3.000 | 3 days and 150 minutes | met | [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56], [57], [58], [59], [60], [61], [62], [63], [64], [65], [66], [67], [68], [69], [70], [71], [72], [73], [74], [75], [76], [77], [78], [122], [123], [124], [125], [126], [142], [143], [144], [145], [146] |
| 2026-01-26 to 2026-02-01 | 2026-01-26 to 2026-01-30 | 3 | 145 or 155 | 2.417 or 2.583 | 3 days and 150 minutes | cannot be determined | [79], [80], [81], [82], [83], [84], [85], [86], [87], [88], [89], [90], [91], [92], [127], [128], [129], [130], [131], [132], [133], [134], [135], [136], [137], [138], [74], [93], [75], [76], [94], [95], [96], [97], [98], [99], [100], [101], [139], [140], [141], [142], [143], [144], [145], [146] |

Calculation ledger:

| Date | Encounter | Service | Included | Contact minutes | Reason | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-01-05 | HG-E101 | individual | included | 50 | Eligible attended patient therapy under the effective plan. | [6], [7], [8], [9], [10] |
| 2026-01-06 | HG-E102 | group | included | 45 | Eligible attended patient therapy under the effective plan. | [11], [12], [13], [14], [15], [16], [17], [18], [19] |
| 2026-01-08 | HG-E103 | individual | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [102], [103], [104], [105] |
| 2026-01-09 | HG-E104 | family | included | 45 | Eligible attended patient therapy under the effective plan. | [20], [21], [22], [23], [24], [25], [26], [27] |
| 2026-01-12 | HG-E105 | group | included | 75 | Eligible attended patient therapy under the effective plan. | [28], [29], [30], [31], [32], [33], [34], [35] |
| 2026-01-13 | HG-E106 | medication | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [106], [107], [108], [109], [110] |
| 2026-01-14 | HG-E107 | individual | included | 45 | Eligible attended patient therapy under the effective plan. | [36], [37], [38] |
| 2026-01-15 | HG-E108 | group | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [111], [112], [113], [114] |
| 2026-01-16 | HG-E109 | collateral | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [115], [116], [117], [118], [119], [120], [121] |
| 2026-01-19 | HG-E110 | group | included | 60 | Eligible attended patient therapy under the effective plan. | [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56], [57], [58], [59], [60], [61] |
| 2026-01-19 | HG-E111 | individual | included | 30 | Eligible attended patient therapy under the effective plan. | [62], [63], [64], [65], [66] |
| 2026-01-21 | HG-E112 | individual | included | 45 | Eligible attended patient therapy under the effective plan. | [67], [68], [69], [70], [71], [72] |
| 2026-01-22 | HG-E113 | group | included | 45 | Eligible attended patient therapy under the effective plan. | [73], [74], [75], [76], [77], [78] |
| 2026-01-23 | HG-E114 | coordination | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [122], [123], [124], [125], [126] |
| 2026-01-26 | HG-E115 | individual | included | 40 or 50 | Eligible attended patient therapy under the effective plan. | [79], [80], [81], [82], [83], [84], [85], [86], [87], [88], [89], [90], [91], [92] |
| 2026-01-27 | HG-E116 | group | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [127], [128], [129], [130], [131], [132], [133], [134], [135], [136] |
| 2026-01-28 | HG-E117 | individual | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [137], [138] |
| 2026-01-29 | HG-E118 | group | included | 75 | Eligible attended patient therapy under the effective plan. | [74], [93], [75], [76], [94], [95] |
| 2026-01-30 | HG-E119 | family | included | 30 | Eligible attended patient therapy under the effective plan. | [96], [97], [98], [99], [100], [101] |
| 2026-01-30 | HG-E120 | medication | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [139], [140], [141] |

Supported event interpretations below are alternatives for the same encounter, rather than additional visits. Dates, service types, attendance, and durations within each interpretation stay together.

- HG-E115, alternative 1: 2026-01-26, individual, attended, patient present yes, 40 minutes; eligible yes, within review window yes; choices event:HG-E115=0, event:harbor grove behavioral health::HG-M042:HG-E115=2026-01-26:individual:attended:True:40. [85], [86], [87], [88], [89], [90], [91], [92]
- HG-E115, alternative 2: 2026-01-26, individual, attended, patient present yes, 50 minutes; eligible yes, within review window yes; choices event:HG-E115=1, event:harbor grove behavioral health::HG-M042:HG-E115=2026-01-26:individual:attended:True:50. [79], [80], [81], [82], [83], [84]

Reconciliation decisions:

- HG-E101, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [6], [7], [8], [9], [10]
- HG-E101, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [6], [7], [8], [9]
- HG-E102, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [11], [12], [13], [14], [15], [16], [17], [18], [19]
- HG-E102, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [11], [12], [13], [14], [15], [16], [17], [18]
- HG-E103, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [102], [103], [104], [105]
- HG-E103, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [102], [103], [104], [105]
- HG-E104, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [20], [21], [22], [23], [24], [25], [26], [27]
- HG-E104, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [21], [22], [23], [24], [25], [26], [27]
- HG-E105, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [28], [29], [30], [31], [32], [33], [34], [35]
- HG-E105, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [28], [29], [30], [32], [33], [34], [35]
- HG-E106, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [106], [107], [108], [109], [110]
- HG-E106, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [107], [108], [109], [110]
- HG-E107, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [36], [37], [38]
- HG-E107, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [37], [38]
- HG-E108, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [111], [112], [113], [114]
- HG-E108, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [111], [112], [113], [114]
- HG-E109, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [115], [116], [117], [118], [119], [120], [121]
- HG-E109, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [117], [118], [119], [120], [121]
- HG-E110, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56], [57], [58], [59], [60], [61]
- HG-E110, departure (established): Apply the scoped correction to matching fields, not receipt order. [55], [56], [57]
- HG-E110, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56], [57], [58], [59], [60], [61]
- HG-E111, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [62], [63], [64], [65], [66]
- HG-E111, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [62], [63], [64], [65], [66]
- HG-E112, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [67], [68], [69], [70], [71], [72]
- HG-E112, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [67], [68], [69], [70], [71], [72]
- HG-E113, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [73], [74], [75], [76], [77], [78]
- HG-E113, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [73], [74], [75], [76], [77], [78]
- HG-E114, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [122], [123], [124], [125], [126]
- HG-E114, duration (missing_evidence): Intersect attendance with activity and remove breaks for each interpretation. [122], [123], [124], [125], [126]
- HG-E115, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [79], [80], [81], [82], [83], [84], [85], [86], [87], [88], [89], [90], [91], [92]
- HG-E115, duration (conflicting_evidence): Intersect attendance with activity and remove breaks for each interpretation. [79], [80], [81], [82], [83], [84], [85], [86], [87], [88], [89], [90], [91], [92]
- HG-E116, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [127], [128], [129], [130], [131], [132], [133], [134], [135], [136]
- HG-E116, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [127], [128]
- HG-E117, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [137], [138]
- HG-E117, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [137], [138]
- HG-E118, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [74], [93], [75], [76], [94], [95]
- HG-E118, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [74], [93], [75], [76], [94], [95]
- HG-E119, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [96], [97], [98], [99], [100], [101]
- HG-E119, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [96], [97], [98], [99], [100], [101]
- HG-E120, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [139], [140], [141]
- HG-E120, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [139], [140], [141]


Records with no extracted care contact:

- BH-D001: 0 assessment claims and 0 observations; no additional session is counted. Administrative quantities and measure reviews do not establish delivered contacts. [1]
- BH-D003: 0 assessment claims and 6 observations; no additional session is counted. Administrative quantities and measure reviews do not establish delivered contacts. [2]
- BH-D013: 1 assessment claims and 4 observations; no additional session is counted. Administrative quantities and measure reviews do not establish delivered contacts. [3]
- BH-D014: 1 assessment claims and 1 observations; no additional session is counted. Administrative quantities and measure reviews do not establish delivered contacts. [4]
- BH-D115: 1 assessment claims and 5 observations; no additional session is counted. Administrative quantities and measure reviews do not establish delivered contacts. [5]

Unresolved conclusions and limitations:

- 2026-01-05 to 2026-01-30, therapy minutes: Values are discrete alternatives from consistent source interpretations.
- Week of 2026-01-26: Supported interpretations disagree, duration is missing, or week coverage is incomplete.

Source passages:

[1] BH-D001, group_authorization_letter.txt, lines 1-15: Document ID: BH-D001 SYNTHETIC TRAINING RECORD — Entirely fictional patient and organization.  Harbor Grove Behavioral Health Administrative correspondence received 2026-01-04, 15:26 local Member: Rowan Mercer | DOB: 1991-04-12 | MRN: HG-M042 Authorization: HG-A260104-88  To: Outpatient program authorization desk The requested group service authorization is approved for the period January 5, 2026 through January 30, 2026. Authorized quantity: 8 group sessions. One authorization unit represents one scheduled group session. The service description is outpatient therapeutic group work supporting the submitted behavioral health treatment plan. This letter does not authorize individual therapy, family therapy, or medication appointments under the group service quantity.  The approved period permits the practice to arrange group appointments within the indicated dates. Scheduling remains the responsibility of Harbor Grove Behavioral Health and the member. Changes in appointment dates within the approved period may be made by the scheduling desk.   Administrative entry, N. Ellis, 2026-01-05, 08:05 local: Letter attached to the program account. Rowan was informed that the office would send a weekly appointment list. Scheduling staff will use the approved group quantity when arranging appointments. No service attendance record accompanies this letter.
[2] BH-D003, signed_treatment_plan_jan05.txt, lines 1-20: Document ID: BH-D003 SYNTHETIC TRAINING RECORD — Entirely fictional patient and organization.  Harbor Grove Behavioral Health | Outpatient treatment plan Rowan Mercer | DOB 1991-04-12 | MRN HG-M042 Episode dates: 2026-01-05 through 2026-01-30 Prepared by Mara Voss, LCSW; signed 2026-01-05, 13:05 local Patient agreement recorded 2026-01-05, 13:12 local  Presenting needs: depressed mood, sleep disruption, anxiety about resuming work responsibilities, and avoidance of tasks and communication. Rowan wishes to improve follow-through without waiting for anxiety to disappear. Partner support is available but repeated reminders sometimes increase tension. The treatment team will combine individual practice, therapeutic group activities, and family work when Rowan is present.  Local treatment participation goal: at least 3 therapy days and at least 150 minutes of patient-present therapy in each Monday–Sunday week. A therapy day is a calendar day on which Rowan participates in individual, group, or family psychotherapy. Patient-present individual, group, and family therapy contribute to the minute goal. Medication management, contacts with collateral informants only, and care coordination do not contribute. This is the program's individualized treatment-plan goal for Rowan.  Goal 1: improve daily activity and task initiation. Rowan will select manageable activities, track attempts, and review barriers with the individual therapist. The team will emphasize completion of useful steps rather than judging the day by mood alone.  Goal 2: improve coping with anxiety and disrupted sleep. Rowan will practice one grounding or paced-breathing exercise and establish a consistent morning routine. Group participation will provide opportunities to rehearse skills and hear alternative approaches.  Goal 3: support a workable return to employment. Individual sessions will address avoided communication and gradual preparation. Family sessions may address how Rowan can request help and how the partner can offer support without taking over tasks.  Review: assess participation, symptoms, and practical functioning during the episode. Adjust the schedule when clinically indicated or when access barriers arise.
[3] BH-D013, symptom_measure_review_jan16.txt, lines 1-15: Document ID: BH-D013 SYNTHETIC TRAINING RECORD — Entirely fictional patient and organization.  Harbor Grove Behavioral Health | Measurement review Rowan Mercer | DOB 1991-04-12 | MRN HG-M042 Instrument: PHQ-9 | Patient portal form HG-Q116 Completed by patient: 2026-01-16, 08:17 local Total score: 14 Reviewed by Mara Voss, LCSW, 2026-01-16, 09:10 local  The submitted score is lower than the intake score of 18 recorded on January 5. In the optional update field, Rowan wrote that getting out of the apartment had become a little easier, while thinking about work continued to make them want to put things off. Rowan also described sleep as inconsistent. No additional questionnaire was submitted with this update.  Clinician review: the score and recent individual-session material suggest some improvement in depressive symptoms. Persistent avoidance, difficulty initiating work communication, and sleep disruption remain clinically relevant. Rowan has attempted small activities and communication practice but has not yet established a reliable routine. Continue the current therapeutic focus and review functioning alongside symptom change during the next direct appointment.  This entry records review of the portal submission; no clinical appointment occurred at the time of review. The form remains attached to the measurement tab with its original completion date.
[4] BH-D014, imported_measure_summary_received_jan26.txt, lines 1-19: Document ID: BH-D014 SYNTHETIC TRAINING RECORD — Entirely fictional patient and organization.  Harbor Grove Behavioral Health | Administrative import receipt Rowan Mercer | DOB 1991-04-12 | MRN HG-M042 Received into chart: 2026-01-26, 07:44 local Source: program measurement summary batch HG-MEAS-0126 Import operator: N. Ellis  The batch received this morning contains the following measurement summary for the outpatient episode. The source record identifies the patient portal submission retained by the treatment team.  Measure | Result | Date completed | Source form PHQ-9   | 14     | 2026-01-16     | HG-Q116  Source review excerpt, Mara Voss, LCSW: some improvement in depressive symptoms; ongoing avoidance of work communication and inconsistent sleep. Continue current therapeutic focus and review practical functioning at the next direct appointment. Original clinician review timestamp: January 16, 2026, 09:10 local.  Import detail: copied result from the January 16 portal form. January 26 is the date the summary was received and filed. No newly completed patient questionnaire is included in this batch. The source form identifier and original completion date were retained in the imported row.   The measurement tab continues to hold the original patient submission. This receipt was entered by the administrative desk and does not document a visit with Rowan.
[5] BH-D115, BH-D115_symptom_measure_review_2026-01-30.txt, lines 1-16: Document ID: BH-D115 HARBOR GROVE BEHAVIORAL HEALTH Symptom questionnaire and chart review Rowan Mercer | DOB: 1991-04-12 | MRN: HG-M042 Questionnaire completed January 30, 2026, 12:42 PHQ-9 total: 10. Item 9: 0.  Rowan completed the questionnaire before the afternoon appointment. The patient continued to endorse sleep difficulty and trouble sustaining usual activities, with fewer days of pervasive low mood than reported at intake. The form was available to the treating clinician for review with the patient's account of functioning.  Clinician review, January 30: Rowan shows partial improvement, with persistent avoidance and meaningful functional impact around returning to work. The patient has taken some initial steps, including drafting and sending a message, but continues to delay follow-up and becomes anxious when a task expands beyond a narrowly defined action. Sleep disruption remains an intermittent barrier to establishing a steadier daytime routine.  Current assessment reflects both the symptom questionnaire and Rowan's reported functioning. Continued treatment is appropriate given the remaining difficulties with follow-through and work-related functioning. Recommend continuity of the established individual and group schedule and continued use of small, observable approach tasks. Family support may help the patient carry out the agreed tasks between appointments.  This entry records questionnaire review within ongoing care and is not a separate treatment appointment. No additional patient-contact interval is claimed in this entry.  Electronically signed: Mira Patel, LCSW | January 30, 2026, 16:20
[6] BH-D002, intake_and_individual_jan05.txt, lines 6-6: Encounter HG-E101 | Service date 2026-01-05
[7] BH-D002, intake_and_individual_jan05.txt, lines 8-8: Patient-present individual therapy: 09:00–09:50 local; completed, 50 minutes.
[8] BH-D002, intake_and_individual_jan05.txt, lines 8-8: completed, 50 minutes.
[9] BH-D002, intake_and_individual_jan05.txt, lines 13-13: Rowan arrived independently and participated throughout the appointment.
[10] BH-D006, early_appointment_status_export.txt, lines 10-10: HG-E101   | Jan05 | Individual therapy     | 09:00–09:50    | Completed
[11] BH-D004, group_facilitator_jan06.txt, lines 5-5: Service date 2026-01-06 | Group scheduled 10:00–11:30 local
[12] BH-D004, group_facilitator_jan06.txt, lines 7-7: Facilitator: Leena Park, LPC
[13] BH-D004, group_facilitator_jan06.txt, lines 12-12: The whole group took a break from 10:45 to 11:00. No therapy was conducted during that interval.
[14] BH-D004, group_facilitator_jan06.txt, lines 14-14: The patient attendance roster is maintained by the group desk.
[15] BH-D005, early_group_attendance_roster.txt, lines 10-10: 2026-01-06 | HG-E102   | 10:00–11:30    | 10:15           | 11:15            | Attended part
[16] BH-D005, early_group_attendance_roster.txt, lines 13-13: Departure was marked when Rowan returned their visitor badge. Rowan did not re-enter the group room after departing.
[17] BH-D005, early_group_attendance_roster.txt, lines 13-13: Rowan advised the facilitator that they would need to leave early for a previously arranged ride.
[18] BH-D005, early_group_attendance_roster.txt, lines 13-13: Rowan called from the building entrance to say they were running behind after difficulty finding parking.
[19] BH-D006, early_appointment_status_export.txt, lines 11-11: HG-E102   | Jan06 | Coping skills group    | 10:00–11:30    | Attended part
[20] BH-D006, early_appointment_status_export.txt, lines 13-13: HG-E104   | Jan09 | Family therapy         | 14:00–14:45    | Completed
[21] BH-D007, family_primary_jan09.txt, lines 6-6: Encounter HG-E104 | 2026-01-09, 14:00–14:45 local
[22] BH-D007, family_primary_jan09.txt, lines 7-7: Present: Rowan and partner, Casey Mercer
[23] BH-D007, family_primary_jan09.txt, lines 9-9: Patient-present family therapy duration: 45 minutes
[24] BH-D007, family_primary_jan09.txt, lines 10-10: Mara Voss signed 2026-01-09, 16:24 local
[25] BH-D008, family_cofacilitator_jan09.txt, lines 6-6: Encounter HG-E104 | Date 2026-01-09 | 14:00–14:45 local
[26] BH-D008, family_cofacilitator_jan09.txt, lines 8-8: Participants: Rowan Mercer and Casey Mercer; both present for the full 45 minutes
[27] BH-D008, family_cofacilitator_jan09.txt, lines 8-8: both present for the full 45 minutes
[28] BH-D005, early_group_attendance_roster.txt, lines 11-11: 2026-01-12 | HG-E105   | 10:00–11:30    | 10:00           | 11:30            | Attended full
[29] BH-D005, early_group_attendance_roster.txt, lines 15-15: No transport concern was reported at that time.
[30] BH-D005, early_group_attendance_roster.txt, lines 15-15: Rowan checked in before the group began and remained until the group was released.
[31] BH-D006, early_appointment_status_export.txt, lines 14-14: HG-E105   | Jan12 | Coping skills group    | 10:00–11:30    | Completed
[32] BH-D009, group_facilitator_jan12.txt, lines 6-6: Service date 2026-01-12 | Scheduled group 10:00–11:30 local
[33] BH-D009, group_facilitator_jan12.txt, lines 7-7: Facilitator: Leena Park, LPC
[34] BH-D009, group_facilitator_jan12.txt, lines 12-12: Group break: 10:40–10:55; no therapeutic activity occurred during the break.
[35] BH-D009, group_facilitator_jan12.txt, lines 16-16: Attendance is recorded on the group desk roster.
[36] BH-D006, early_appointment_status_export.txt, lines 16-16: HG-E107   | Jan14 | Individual therapy     | 11:00–11:45    | Completed
[37] BH-D011, individual_therapy_jan14.txt, lines 6-6: Encounter HG-E107 | Date 2026-01-14
[38] BH-D011, individual_therapy_jan14.txt, lines 7-7: Patient-present session 11:00–11:45 local; completed, 45 minutes
[39] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 3-3: Skills group clinical record | Service date: January 19, 2026
[40] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 4-4: Group encounter: HG-E110 | Facilitator: Leah Chen, LCSW
[41] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 5-5: Patient chart: Rowan Mercer | DOB: 1991-04-12 | MRN: HG-M042
[42] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 6-6: Scheduled group: 10:00–11:30. Nontherapeutic break: 10:45–11:00.
[43] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 8-8: The break was for restroom use and refreshments; there was no facilitated discussion, assigned therapeutic activity, or patient treatment during that interval.
[44] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 10-10: Patient-specific arrival and departure are maintained on the attendance roster.
[45] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 4-4: Service date: January 19, 2026 | Group encounter: HG-E110
[46] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 5-5: Patient: Rowan Mercer | DOB: 1991-04-12 | MRN: HG-M042
[47] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 8-8: Scheduled opening: 10:00 | Scheduled closing: 11:30
[48] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 9-9: Patient arrival: 10:00 | Patient departure: 11:30 | Status: Attended
[49] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 10-10: Roster disposition: Final, signed
[50] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 12-12: This is the patient row from the facilitator's attendance sheet.
[51] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 16-16: The staff member closing the roster certified the patient row as shown at the time of signing.
[52] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 16-16: This roster is the original signed attendance entry for the listed service date.
[53] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 18-18: Electronically signed: Leah Chen, LCSW | January 19, 2026, 12:14
[54] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 19-19: Document status: Final
[55] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 7-7: Correction: Patient departure for HG-E110 is 11:15, replacing the original roster value of 11:30. Patient arrival remains 10:00.
[56] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 11-11: The original signed roster is retained in the chart with this correction attached to its attendance entry.
[57] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 11-11: This correction applies only to Rowan Mercer's departure field on the January 19 group attendance roster. It does not change the group service date, scheduled opening or closing, the break recorded in the group clinical note, or the separate individual appointment.
[58] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 11-11: Service date: January 19, 2026 | Group encounter: HG-E110
[59] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 13-13: Scheduled opening: 10:00 | Scheduled closing: 11:30
[60] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 14-14: Patient arrival: 10:00 | Patient departure: 11:30 | Status: Attended
[61] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 20-20: This is a retransmission of the January 19 roster for HG-E110. The received copy contains no new clinician signature and records no additional visit.
[62] BH-D105, BH-D105_individual_2026-01-19.txt, lines 3-3: Individual psychotherapy | Encounter HG-E111
[63] BH-D105, BH-D105_individual_2026-01-19.txt, lines 5-5: January 19, 2026 | In person
[64] BH-D105, BH-D105_individual_2026-01-19.txt, lines 6-6: Completed: 30 minutes
[65] BH-D105, BH-D105_individual_2026-01-19.txt, lines 6-6: Patient contact: 11:15–11:45 | Completed: 30 minutes
[66] BH-D105, BH-D105_individual_2026-01-19.txt, lines 11-11: Rowan participated throughout the individual contact
[67] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Connection was lost from 13:20–13:30; there was no therapeutic contact during that interval.
[68] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Patient contact occurred 13:00–13:20 and 13:30–13:55.
[69] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: The reconnection continued the same clinical encounter under original appointment HG-A112.
[70] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Total patient psychotherapy contact: 45 minutes.
[71] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 15-15: ATTACHED PLATFORM CONNECTION EXPORT
[72] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 16-18: Appointment ID | Call ID | Connected | Ended HG-A112 | VC-112A | January 21 13:00 | January 21 13:20 HG-A112 | VC-112B | January 21 13:30 | January 21 13:55
[73] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 7-7: January 22, 2026 | Encounter HG-E113
[74] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 8-8: Scheduled group 10:00–11:30. Nontherapeutic break 10:45–11:00.
[75] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 13-13: Scheduled group 10:00–11:30. Nontherapeutic break 10:45–11:00.
[76] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 17-17: For both dates, the break was unstructured time without therapeutic activity or facilitator treatment. Patient arrival, departure, and attendance status are entered in the separate attendance register.
[77] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 9-9: January 22 | HG-E113 | Skills group | 10:00–11:30 | 10:30 | 11:30 | Attended, late arrival
[78] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 14-14: January 22 attendance attestation: Rowan arrived at 10:30 and remained until the group closed. Signed: Leah Chen, LCSW, January 22, 12:09.
[79] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 3-3: Individual psychotherapy | Encounter HG-E115 | Appointment HG-A115
[80] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 5-5: January 26, 2026 | In person
[81] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 6-6: Clinicians: Mira Patel, LCSW; Nora Ellis, LCSW
[82] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 7-7: Actual patient psychotherapy contact: 09:00–09:50, 50 minutes.
[83] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 15-15: Electronically signed: Mira Patel, LCSW | January 26, 2026, 11:16
[84] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 16-16: Record status: Final
[85] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 4-4: Encounter HG-E115 | Appointment HG-A115 | Service date January 26, 2026
[86] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 6-6: Service: Individual psychotherapy, in person
[87] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 7-7: Actual patient psychotherapy contact: 09:10–09:50, 40 minutes.
[88] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 10-10: Rowan entered the treatment room at 09:10, when we began the session.
[89] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 10-10: The full patient-contact interval for the encounter was 09:10–09:50.
[90] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 14-14: The session concluded with Rowan at 09:50.
[91] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 16-16: Electronically signed: Nora Ellis, LCSW | January 26, 2026, 12:03
[92] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 17-17: Record status: Final
[93] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 12-12: January 29, 2026 | Encounter HG-E118
[94] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 12-12: January 29 | HG-E118 | Skills group | 10:00–11:30 | 10:00 | 11:30 | Attended
[95] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 20-20: January 29 attendance attestation: Rowan was present from opening through closing. Signed: Leah Chen, LCSW, January 29, 12:15.
[96] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 3-3: Family psychotherapy | Encounter HG-E119
[97] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 5-5: January 30, 2026 | In person | Clinician: Mira Patel, LCSW
[98] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 6-6: Therapist session interval: 13:00–13:45, 45 minutes.
[99] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 7-7: Partner only: 13:00–13:15. Rowan present with partner: 13:15–13:45, 30 minutes.
[100] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 7-7: Rowan present with partner: 13:15–13:45, 30 minutes.
[101] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 11-11: Rowan joined at 13:15 and participated through the end of the session.
[102] BH-D006, early_appointment_status_export.txt, lines 12-12: HG-E103   | Jan08 | Individual therapy     | 11:00–11:45    | No show
[103] BH-D006, early_appointment_status_export.txt, lines 20-20: HG-E103 remained unarrived at close of its appointment slot on January 8.
[104] BH-D015, missed_visit_outreach_jan08.txt, lines 6-6: Related appointment: HG-E103, 2026-01-08, 11:00–11:45 local
[105] BH-D015, missed_visit_outreach_jan08.txt, lines 11-11: 11:45: Appointment marked no show. Rowan was not seen for the scheduled individual visit.
[106] BH-D006, early_appointment_status_export.txt, lines 15-15: HG-E106   | Jan13 | Medication management  | 09:00–09:25    | Completed
[107] BH-D010, medication_review_jan13.txt, lines 6-6: Encounter HG-E106 | Date 2026-01-13
[108] BH-D010, medication_review_jan13.txt, lines 7-7: Actual visit 09:00–09:25 local; completed, 25 minutes
[109] BH-D010, medication_review_jan13.txt, lines 11-11: Rowan attended for medication management.
[110] BH-D010, medication_review_jan13.txt, lines 17-17: Service documented: medication review and management only. No separate psychotherapy component was provided or documented.
[111] BH-D006, early_appointment_status_export.txt, lines 17-17: HG-E108   | Jan15 | Coping skills group    | 10:00–11:30    | Clinic cancelled
[112] BH-D006, early_appointment_status_export.txt, lines 20-20: HG-E108 was removed from the active room schedule after staff illness was reported. A cancellation message was released to all registered members.
[113] BH-D016, group_cancellation_notice_jan15.txt, lines 9-9: The coping skills group scheduled for January 15 from 10:00 to 11:30 is cancelled by the clinic because of staff illness.
[114] BH-D016, group_cancellation_notice_jan15.txt, lines 15-15: No group was held and no participants were seen for HG-E108.
[115] BH-D006, early_appointment_status_export.txt, lines 18-18: HG-E109   | Jan16 | Family collateral      | 14:00–14:40    | Completed
[116] BH-D006, early_appointment_status_export.txt, lines 20-20: Appointment HG-E109 was retained as a partner collateral contact after Rowan could not attend.
[117] BH-D012, partner_collateral_jan16.txt, lines 6-6: Encounter HG-E109 | Date 2026-01-16 | 14:00–14:40 local
[118] BH-D012, partner_collateral_jan16.txt, lines 8-8: Participant: Casey Mercer, partner. Rowan was absent for the entire contact.
[119] BH-D012, partner_collateral_jan16.txt, lines 11-11: Casey attended the arranged contact after Rowan advised the office that they could not participate.
[120] BH-D012, partner_collateral_jan16.txt, lines 11-11: This was a collateral discussion with Casey only, focused on observations at home and ways to support the treatment plan.
[121] BH-D012, partner_collateral_jan16.txt, lines 17-17: Rowan did not join in person, by telephone, or by video. No patient-present psychotherapy occurred during this contact.
[122] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 3-3: Care coordination | Encounter HG-E114
[123] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 5-5: January 23, 2026 | 09:00–09:20
[124] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 6-6: Participants: Mira Patel, LCSW, and Daniel Shaw, outside social worker
[125] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 7-7: Patient participation: None. No patient contact occurred.
[126] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 13-13: This contact was between professionals only. Rowan did not join by telephone or video, and no psychotherapy was delivered to the patient during the call.
[127] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 10-10: January 27 | HG-E116 | Skills group | 10:00–11:30 | — | — | No show; patient did not attend
[128] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 16-16: January 27 attendance attestation: Final roster confirms Rowan was absent for the entire group. No patient treatment contact occurred. An outreach message inviting the patient to contact scheduling was left after the group; no clinical discussion occurred. Signed: Leah Chen, LCSW, January 27, 11:54.
[129] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 9-9: Status: DRAFT — UNSIGNED — system populated from scheduled group template
[130] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 10-10: Scheduled service: Skills group, 10:00–11:30
[131] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 11-11: Template attendance text: Patient attended the full session and participated in the skills discussion.
[132] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 18-18: SECTION B — POSTED CHARGE EXTRACT
[133] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 20-20: Service date: January 27, 2026
[134] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 21-21: Description: Group psychotherapy
[135] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 22-22: Quantity charged: 1 group session
[136] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 23-23: Charge status in this export: Posted
[137] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 11-11: January 28 | HG-E117 | Individual | 14:00–14:45 | — | — | Patient cancelled before appointment
[138] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 18-18: January 28 scheduling entry: Cancellation received from patient January 28, 08:12. Rowan reported a personal scheduling conflict. Appointment HG-E117 was cancelled before the scheduled start; no replacement appointment was booked within January 2026. Entered by Ana Reed, January 28, 08:18.
[139] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 5-5: Completed, 20 minutes
[140] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 5-5: January 30, 2026 | 15:00–15:20 | Completed, 20 minutes
[141] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 12-12: The service consisted of medication evaluation and management, including symptom review and medication counseling. No separately documented psychotherapy was provided.
[142] BH-D003, signed_treatment_plan_jan05.txt, lines 6-6: Episode dates: 2026-01-05 through 2026-01-30
[143] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: A therapy day is a calendar day on which Rowan participates in individual, group, or family psychotherapy. Patient-present individual, group, and family therapy contribute to the minute goal. Medication management, contacts with collateral informants only, and care coordination do not contribute. This is the program's individualized treatment-plan goal for Rowan.
[144] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: Local treatment participation goal: at least 3 therapy days and at least 150 minutes of patient-present therapy in each Monday–Sunday week.
[145] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: at least 150 minutes of patient-present therapy
[146] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: at least 3 therapy days

## DEV-02

Task 1: durations; patients Rowan Mercer.

Snapshot: 1. Question: How many therapy minutes and hours did Rowan actually receive during the review period, overall and for each Monday–Sunday week? Show calculations or supporting detail, and report any conclusion the available documents do not settle.

Review window: 2026-01-05 through 2026-01-30, inclusive.

Therapy minutes: **585 or 595** (**9.750 or 9.917 hours**, rounded to 3 decimals).

Monday-Sunday weekly calculations use the review-range contributions below. Thresholds are the documented goals; partial weeks are not silently prorated.

| Calendar week | Reviewed dates | Days | Minutes | Hours | Goal | Decision | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-01-05 to 2026-01-11 | 2026-01-05 to 2026-01-11 | 3 | 140 | 2.333 | 3 days and 150 minutes | not_met | [1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12], [13], [14], [97], [98], [99], [100], [15], [16], [17], [18], [19], [20], [21], [22], [137], [138], [139], [140], [141] |
| 2026-01-12 to 2026-01-18 | 2026-01-12 to 2026-01-18 | 2 | 120 | 2.000 | 3 days and 150 minutes | not_met | [23], [24], [25], [26], [27], [28], [29], [30], [101], [102], [103], [104], [105], [31], [32], [33], [106], [107], [108], [109], [110], [111], [112], [113], [114], [115], [116], [137], [138], [139], [140], [141] |
| 2026-01-19 to 2026-01-25 | 2026-01-19 to 2026-01-25 | 3 | 180 | 3.000 | 3 days and 150 minutes | met | [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56], [57], [58], [59], [60], [61], [62], [63], [64], [65], [66], [67], [68], [69], [70], [71], [72], [73], [117], [118], [119], [120], [121], [137], [138], [139], [140], [141] |
| 2026-01-26 to 2026-02-01 | 2026-01-26 to 2026-01-30 | 3 | 145 or 155 | 2.417 or 2.583 | 3 days and 150 minutes | cannot be determined | [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87], [122], [123], [124], [125], [126], [127], [128], [129], [130], [131], [132], [133], [69], [88], [70], [71], [89], [90], [91], [92], [93], [94], [95], [96], [134], [135], [136], [137], [138], [139], [140], [141] |

Calculation ledger:

| Date | Encounter | Service | Included | Contact minutes | Reason | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-01-05 | HG-E101 | individual | included | 50 | Eligible attended patient therapy under the effective plan. | [1], [2], [3], [4], [5] |
| 2026-01-06 | HG-E102 | group | included | 45 | Eligible attended patient therapy under the effective plan. | [6], [7], [8], [9], [10], [11], [12], [13], [14] |
| 2026-01-08 | HG-E103 | individual | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [97], [98], [99], [100] |
| 2026-01-09 | HG-E104 | family | included | 45 | Eligible attended patient therapy under the effective plan. | [15], [16], [17], [18], [19], [20], [21], [22] |
| 2026-01-12 | HG-E105 | group | included | 75 | Eligible attended patient therapy under the effective plan. | [23], [24], [25], [26], [27], [28], [29], [30] |
| 2026-01-13 | HG-E106 | medication | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [101], [102], [103], [104], [105] |
| 2026-01-14 | HG-E107 | individual | included | 45 | Eligible attended patient therapy under the effective plan. | [31], [32], [33] |
| 2026-01-15 | HG-E108 | group | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [106], [107], [108], [109] |
| 2026-01-16 | HG-E109 | collateral | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [110], [111], [112], [113], [114], [115], [116] |
| 2026-01-19 | HG-E110 | group | included | 60 | Eligible attended patient therapy under the effective plan. | [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56] |
| 2026-01-19 | HG-E111 | individual | included | 30 | Eligible attended patient therapy under the effective plan. | [57], [58], [59], [60], [61] |
| 2026-01-21 | HG-E112 | individual | included | 45 | Eligible attended patient therapy under the effective plan. | [62], [63], [64], [65], [66], [67] |
| 2026-01-22 | HG-E113 | group | included | 45 | Eligible attended patient therapy under the effective plan. | [68], [69], [70], [71], [72], [73] |
| 2026-01-23 | HG-E114 | coordination | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [117], [118], [119], [120], [121] |
| 2026-01-26 | HG-E115 | individual | included | 40 or 50 | Eligible attended patient therapy under the effective plan. | [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87] |
| 2026-01-27 | HG-E116 | group | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [122], [123], [124], [125], [126], [127], [128], [129], [130], [131] |
| 2026-01-28 | HG-E117 | individual | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [132], [133] |
| 2026-01-29 | HG-E118 | group | included | 75 | Eligible attended patient therapy under the effective plan. | [69], [88], [70], [71], [89], [90] |
| 2026-01-30 | HG-E119 | family | included | 30 | Eligible attended patient therapy under the effective plan. | [91], [92], [93], [94], [95], [96] |
| 2026-01-30 | HG-E120 | medication | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [134], [135], [136] |

Supported event interpretations below are alternatives for the same encounter, rather than additional visits. Dates, service types, attendance, and durations within each interpretation stay together.

- HG-E115, alternative 1: 2026-01-26, individual, attended, patient present yes, 40 minutes; eligible yes, within review window yes; choices event:HG-E115=0, event:harbor grove behavioral health::HG-M042:HG-E115=2026-01-26:individual:attended:True:40. [80], [81], [82], [83], [84], [85], [86], [87]
- HG-E115, alternative 2: 2026-01-26, individual, attended, patient present yes, 50 minutes; eligible yes, within review window yes; choices event:HG-E115=1, event:harbor grove behavioral health::HG-M042:HG-E115=2026-01-26:individual:attended:True:50. [74], [75], [76], [77], [78], [79]

Reconciliation decisions:

- HG-E101, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [1], [2], [3], [4], [5]
- HG-E101, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [1], [2], [3], [4]
- HG-E102, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [6], [7], [8], [9], [10], [11], [12], [13], [14]
- HG-E102, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [6], [7], [8], [9], [10], [11], [12], [13]
- HG-E103, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [97], [98], [99], [100]
- HG-E103, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [97], [98], [99], [100]
- HG-E104, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [15], [16], [17], [18], [19], [20], [21], [22]
- HG-E104, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [16], [17], [18], [19], [20], [21], [22]
- HG-E105, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [23], [24], [25], [26], [27], [28], [29], [30]
- HG-E105, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [23], [24], [25], [27], [28], [29], [30]
- HG-E106, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [101], [102], [103], [104], [105]
- HG-E106, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [102], [103], [104], [105]
- HG-E107, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [31], [32], [33]
- HG-E107, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [32], [33]
- HG-E108, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [106], [107], [108], [109]
- HG-E108, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [106], [107], [108], [109]
- HG-E109, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [110], [111], [112], [113], [114], [115], [116]
- HG-E109, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [112], [113], [114], [115], [116]
- HG-E110, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56]
- HG-E110, departure (established): Apply the scoped correction to matching fields, not receipt order. [50], [51], [52]
- HG-E110, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56]
- HG-E111, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [57], [58], [59], [60], [61]
- HG-E111, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [57], [58], [59], [60], [61]
- HG-E112, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [62], [63], [64], [65], [66], [67]
- HG-E112, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [62], [63], [64], [65], [66], [67]
- HG-E113, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [68], [69], [70], [71], [72], [73]
- HG-E113, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [68], [69], [70], [71], [72], [73]
- HG-E114, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [117], [118], [119], [120], [121]
- HG-E114, duration (missing_evidence): Intersect attendance with activity and remove breaks for each interpretation. [117], [118], [119], [120], [121]
- HG-E115, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87]
- HG-E115, duration (conflicting_evidence): Intersect attendance with activity and remove breaks for each interpretation. [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87]
- HG-E116, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [122], [123], [124], [125], [126], [127], [128], [129], [130], [131]
- HG-E116, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [122], [123]
- HG-E117, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [132], [133]
- HG-E117, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [132], [133]
- HG-E118, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [69], [88], [70], [71], [89], [90]
- HG-E118, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [69], [88], [70], [71], [89], [90]
- HG-E119, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [91], [92], [93], [94], [95], [96]
- HG-E119, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [91], [92], [93], [94], [95], [96]
- HG-E120, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [134], [135], [136]
- HG-E120, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [134], [135], [136]


Unresolved conclusions and limitations:

- 2026-01-05 to 2026-01-30, therapy minutes: Values are discrete alternatives from consistent source interpretations.
- Week of 2026-01-26: Supported interpretations disagree, duration is missing, or week coverage is incomplete.

Additional evidence needed:

- patient harbor grove behavioral health::HG-M042, HG-E115, 2026-01-05 through 2026-01-30, duration: Supported records disagree on actual patient-contact duration: 40 or 50 minutes. Obtain an explicit duration correction scoped to patient harbor grove behavioral health::HG-M042, encounter HG-E115, 2026-01-26, identifying which earlier assertion it replaces, or the actual patient-contact start/end times and break record for that encounter. [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87]

Source passages:

[1] BH-D002, intake_and_individual_jan05.txt, lines 6-6: Encounter HG-E101 | Service date 2026-01-05
[2] BH-D002, intake_and_individual_jan05.txt, lines 8-8: Patient-present individual therapy: 09:00–09:50 local; completed, 50 minutes.
[3] BH-D002, intake_and_individual_jan05.txt, lines 8-8: completed, 50 minutes.
[4] BH-D002, intake_and_individual_jan05.txt, lines 13-13: Rowan arrived independently and participated throughout the appointment.
[5] BH-D006, early_appointment_status_export.txt, lines 10-10: HG-E101   | Jan05 | Individual therapy     | 09:00–09:50    | Completed
[6] BH-D004, group_facilitator_jan06.txt, lines 5-5: Service date 2026-01-06 | Group scheduled 10:00–11:30 local
[7] BH-D004, group_facilitator_jan06.txt, lines 7-7: Facilitator: Leena Park, LPC
[8] BH-D004, group_facilitator_jan06.txt, lines 12-12: The whole group took a break from 10:45 to 11:00. No therapy was conducted during that interval.
[9] BH-D004, group_facilitator_jan06.txt, lines 14-14: The patient attendance roster is maintained by the group desk.
[10] BH-D005, early_group_attendance_roster.txt, lines 10-10: 2026-01-06 | HG-E102   | 10:00–11:30    | 10:15           | 11:15            | Attended part
[11] BH-D005, early_group_attendance_roster.txt, lines 13-13: Departure was marked when Rowan returned their visitor badge. Rowan did not re-enter the group room after departing.
[12] BH-D005, early_group_attendance_roster.txt, lines 13-13: Rowan advised the facilitator that they would need to leave early for a previously arranged ride.
[13] BH-D005, early_group_attendance_roster.txt, lines 13-13: Rowan called from the building entrance to say they were running behind after difficulty finding parking.
[14] BH-D006, early_appointment_status_export.txt, lines 11-11: HG-E102   | Jan06 | Coping skills group    | 10:00–11:30    | Attended part
[15] BH-D006, early_appointment_status_export.txt, lines 13-13: HG-E104   | Jan09 | Family therapy         | 14:00–14:45    | Completed
[16] BH-D007, family_primary_jan09.txt, lines 6-6: Encounter HG-E104 | 2026-01-09, 14:00–14:45 local
[17] BH-D007, family_primary_jan09.txt, lines 7-7: Present: Rowan and partner, Casey Mercer
[18] BH-D007, family_primary_jan09.txt, lines 9-9: Patient-present family therapy duration: 45 minutes
[19] BH-D007, family_primary_jan09.txt, lines 10-10: Mara Voss signed 2026-01-09, 16:24 local
[20] BH-D008, family_cofacilitator_jan09.txt, lines 6-6: Encounter HG-E104 | Date 2026-01-09 | 14:00–14:45 local
[21] BH-D008, family_cofacilitator_jan09.txt, lines 8-8: Participants: Rowan Mercer and Casey Mercer; both present for the full 45 minutes
[22] BH-D008, family_cofacilitator_jan09.txt, lines 8-8: both present for the full 45 minutes
[23] BH-D005, early_group_attendance_roster.txt, lines 11-11: 2026-01-12 | HG-E105   | 10:00–11:30    | 10:00           | 11:30            | Attended full
[24] BH-D005, early_group_attendance_roster.txt, lines 15-15: No transport concern was reported at that time.
[25] BH-D005, early_group_attendance_roster.txt, lines 15-15: Rowan checked in before the group began and remained until the group was released.
[26] BH-D006, early_appointment_status_export.txt, lines 14-14: HG-E105   | Jan12 | Coping skills group    | 10:00–11:30    | Completed
[27] BH-D009, group_facilitator_jan12.txt, lines 6-6: Service date 2026-01-12 | Scheduled group 10:00–11:30 local
[28] BH-D009, group_facilitator_jan12.txt, lines 7-7: Facilitator: Leena Park, LPC
[29] BH-D009, group_facilitator_jan12.txt, lines 12-12: Group break: 10:40–10:55; no therapeutic activity occurred during the break.
[30] BH-D009, group_facilitator_jan12.txt, lines 16-16: Attendance is recorded on the group desk roster.
[31] BH-D006, early_appointment_status_export.txt, lines 16-16: HG-E107   | Jan14 | Individual therapy     | 11:00–11:45    | Completed
[32] BH-D011, individual_therapy_jan14.txt, lines 6-6: Encounter HG-E107 | Date 2026-01-14
[33] BH-D011, individual_therapy_jan14.txt, lines 7-7: Patient-present session 11:00–11:45 local; completed, 45 minutes
[34] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 3-3: Skills group clinical record | Service date: January 19, 2026
[35] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 4-4: Group encounter: HG-E110 | Facilitator: Leah Chen, LCSW
[36] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 5-5: Patient chart: Rowan Mercer | DOB: 1991-04-12 | MRN: HG-M042
[37] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 6-6: Scheduled group: 10:00–11:30. Nontherapeutic break: 10:45–11:00.
[38] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 8-8: The break was for restroom use and refreshments; there was no facilitated discussion, assigned therapeutic activity, or patient treatment during that interval.
[39] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 10-10: Patient-specific arrival and departure are maintained on the attendance roster.
[40] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 4-4: Service date: January 19, 2026 | Group encounter: HG-E110
[41] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 5-5: Patient: Rowan Mercer | DOB: 1991-04-12 | MRN: HG-M042
[42] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 8-8: Scheduled opening: 10:00 | Scheduled closing: 11:30
[43] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 9-9: Patient arrival: 10:00 | Patient departure: 11:30 | Status: Attended
[44] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 10-10: Roster disposition: Final, signed
[45] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 12-12: This is the patient row from the facilitator's attendance sheet.
[46] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 16-16: The staff member closing the roster certified the patient row as shown at the time of signing.
[47] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 16-16: This roster is the original signed attendance entry for the listed service date.
[48] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 18-18: Electronically signed: Leah Chen, LCSW | January 19, 2026, 12:14
[49] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 19-19: Document status: Final
[50] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 7-7: Correction: Patient departure for HG-E110 is 11:15, replacing the original roster value of 11:30. Patient arrival remains 10:00.
[51] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 11-11: The original signed roster is retained in the chart with this correction attached to its attendance entry.
[52] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 11-11: This correction applies only to Rowan Mercer's departure field on the January 19 group attendance roster. It does not change the group service date, scheduled opening or closing, the break recorded in the group clinical note, or the separate individual appointment.
[53] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 11-11: Service date: January 19, 2026 | Group encounter: HG-E110
[54] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 13-13: Scheduled opening: 10:00 | Scheduled closing: 11:30
[55] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 14-14: Patient arrival: 10:00 | Patient departure: 11:30 | Status: Attended
[56] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 20-20: This is a retransmission of the January 19 roster for HG-E110. The received copy contains no new clinician signature and records no additional visit.
[57] BH-D105, BH-D105_individual_2026-01-19.txt, lines 3-3: Individual psychotherapy | Encounter HG-E111
[58] BH-D105, BH-D105_individual_2026-01-19.txt, lines 5-5: January 19, 2026 | In person
[59] BH-D105, BH-D105_individual_2026-01-19.txt, lines 6-6: Completed: 30 minutes
[60] BH-D105, BH-D105_individual_2026-01-19.txt, lines 6-6: Patient contact: 11:15–11:45 | Completed: 30 minutes
[61] BH-D105, BH-D105_individual_2026-01-19.txt, lines 11-11: Rowan participated throughout the individual contact
[62] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Connection was lost from 13:20–13:30; there was no therapeutic contact during that interval.
[63] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Patient contact occurred 13:00–13:20 and 13:30–13:55.
[64] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: The reconnection continued the same clinical encounter under original appointment HG-A112.
[65] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Total patient psychotherapy contact: 45 minutes.
[66] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 15-15: ATTACHED PLATFORM CONNECTION EXPORT
[67] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 16-18: Appointment ID | Call ID | Connected | Ended HG-A112 | VC-112A | January 21 13:00 | January 21 13:20 HG-A112 | VC-112B | January 21 13:30 | January 21 13:55
[68] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 7-7: January 22, 2026 | Encounter HG-E113
[69] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 8-8: Scheduled group 10:00–11:30. Nontherapeutic break 10:45–11:00.
[70] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 13-13: Scheduled group 10:00–11:30. Nontherapeutic break 10:45–11:00.
[71] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 17-17: For both dates, the break was unstructured time without therapeutic activity or facilitator treatment. Patient arrival, departure, and attendance status are entered in the separate attendance register.
[72] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 9-9: January 22 | HG-E113 | Skills group | 10:00–11:30 | 10:30 | 11:30 | Attended, late arrival
[73] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 14-14: January 22 attendance attestation: Rowan arrived at 10:30 and remained until the group closed. Signed: Leah Chen, LCSW, January 22, 12:09.
[74] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 3-3: Individual psychotherapy | Encounter HG-E115 | Appointment HG-A115
[75] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 5-5: January 26, 2026 | In person
[76] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 6-6: Clinicians: Mira Patel, LCSW; Nora Ellis, LCSW
[77] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 7-7: Actual patient psychotherapy contact: 09:00–09:50, 50 minutes.
[78] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 15-15: Electronically signed: Mira Patel, LCSW | January 26, 2026, 11:16
[79] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 16-16: Record status: Final
[80] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 4-4: Encounter HG-E115 | Appointment HG-A115 | Service date January 26, 2026
[81] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 6-6: Service: Individual psychotherapy, in person
[82] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 7-7: Actual patient psychotherapy contact: 09:10–09:50, 40 minutes.
[83] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 10-10: Rowan entered the treatment room at 09:10, when we began the session.
[84] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 10-10: The full patient-contact interval for the encounter was 09:10–09:50.
[85] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 14-14: The session concluded with Rowan at 09:50.
[86] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 16-16: Electronically signed: Nora Ellis, LCSW | January 26, 2026, 12:03
[87] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 17-17: Record status: Final
[88] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 12-12: January 29, 2026 | Encounter HG-E118
[89] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 12-12: January 29 | HG-E118 | Skills group | 10:00–11:30 | 10:00 | 11:30 | Attended
[90] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 20-20: January 29 attendance attestation: Rowan was present from opening through closing. Signed: Leah Chen, LCSW, January 29, 12:15.
[91] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 3-3: Family psychotherapy | Encounter HG-E119
[92] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 5-5: January 30, 2026 | In person | Clinician: Mira Patel, LCSW
[93] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 6-6: Therapist session interval: 13:00–13:45, 45 minutes.
[94] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 7-7: Partner only: 13:00–13:15. Rowan present with partner: 13:15–13:45, 30 minutes.
[95] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 7-7: Rowan present with partner: 13:15–13:45, 30 minutes.
[96] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 11-11: Rowan joined at 13:15 and participated through the end of the session.
[97] BH-D006, early_appointment_status_export.txt, lines 12-12: HG-E103   | Jan08 | Individual therapy     | 11:00–11:45    | No show
[98] BH-D006, early_appointment_status_export.txt, lines 20-20: HG-E103 remained unarrived at close of its appointment slot on January 8.
[99] BH-D015, missed_visit_outreach_jan08.txt, lines 6-6: Related appointment: HG-E103, 2026-01-08, 11:00–11:45 local
[100] BH-D015, missed_visit_outreach_jan08.txt, lines 11-11: 11:45: Appointment marked no show. Rowan was not seen for the scheduled individual visit.
[101] BH-D006, early_appointment_status_export.txt, lines 15-15: HG-E106   | Jan13 | Medication management  | 09:00–09:25    | Completed
[102] BH-D010, medication_review_jan13.txt, lines 6-6: Encounter HG-E106 | Date 2026-01-13
[103] BH-D010, medication_review_jan13.txt, lines 7-7: Actual visit 09:00–09:25 local; completed, 25 minutes
[104] BH-D010, medication_review_jan13.txt, lines 11-11: Rowan attended for medication management.
[105] BH-D010, medication_review_jan13.txt, lines 17-17: Service documented: medication review and management only. No separate psychotherapy component was provided or documented.
[106] BH-D006, early_appointment_status_export.txt, lines 17-17: HG-E108   | Jan15 | Coping skills group    | 10:00–11:30    | Clinic cancelled
[107] BH-D006, early_appointment_status_export.txt, lines 20-20: HG-E108 was removed from the active room schedule after staff illness was reported. A cancellation message was released to all registered members.
[108] BH-D016, group_cancellation_notice_jan15.txt, lines 9-9: The coping skills group scheduled for January 15 from 10:00 to 11:30 is cancelled by the clinic because of staff illness.
[109] BH-D016, group_cancellation_notice_jan15.txt, lines 15-15: No group was held and no participants were seen for HG-E108.
[110] BH-D006, early_appointment_status_export.txt, lines 18-18: HG-E109   | Jan16 | Family collateral      | 14:00–14:40    | Completed
[111] BH-D006, early_appointment_status_export.txt, lines 20-20: Appointment HG-E109 was retained as a partner collateral contact after Rowan could not attend.
[112] BH-D012, partner_collateral_jan16.txt, lines 6-6: Encounter HG-E109 | Date 2026-01-16 | 14:00–14:40 local
[113] BH-D012, partner_collateral_jan16.txt, lines 8-8: Participant: Casey Mercer, partner. Rowan was absent for the entire contact.
[114] BH-D012, partner_collateral_jan16.txt, lines 11-11: Casey attended the arranged contact after Rowan advised the office that they could not participate.
[115] BH-D012, partner_collateral_jan16.txt, lines 11-11: This was a collateral discussion with Casey only, focused on observations at home and ways to support the treatment plan.
[116] BH-D012, partner_collateral_jan16.txt, lines 17-17: Rowan did not join in person, by telephone, or by video. No patient-present psychotherapy occurred during this contact.
[117] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 3-3: Care coordination | Encounter HG-E114
[118] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 5-5: January 23, 2026 | 09:00–09:20
[119] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 6-6: Participants: Mira Patel, LCSW, and Daniel Shaw, outside social worker
[120] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 7-7: Patient participation: None. No patient contact occurred.
[121] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 13-13: This contact was between professionals only. Rowan did not join by telephone or video, and no psychotherapy was delivered to the patient during the call.
[122] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 10-10: January 27 | HG-E116 | Skills group | 10:00–11:30 | — | — | No show; patient did not attend
[123] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 16-16: January 27 attendance attestation: Final roster confirms Rowan was absent for the entire group. No patient treatment contact occurred. An outreach message inviting the patient to contact scheduling was left after the group; no clinical discussion occurred. Signed: Leah Chen, LCSW, January 27, 11:54.
[124] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 9-9: Status: DRAFT — UNSIGNED — system populated from scheduled group template
[125] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 10-10: Scheduled service: Skills group, 10:00–11:30
[126] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 11-11: Template attendance text: Patient attended the full session and participated in the skills discussion.
[127] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 18-18: SECTION B — POSTED CHARGE EXTRACT
[128] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 20-20: Service date: January 27, 2026
[129] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 21-21: Description: Group psychotherapy
[130] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 22-22: Quantity charged: 1 group session
[131] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 23-23: Charge status in this export: Posted
[132] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 11-11: January 28 | HG-E117 | Individual | 14:00–14:45 | — | — | Patient cancelled before appointment
[133] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 18-18: January 28 scheduling entry: Cancellation received from patient January 28, 08:12. Rowan reported a personal scheduling conflict. Appointment HG-E117 was cancelled before the scheduled start; no replacement appointment was booked within January 2026. Entered by Ana Reed, January 28, 08:18.
[134] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 5-5: Completed, 20 minutes
[135] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 5-5: January 30, 2026 | 15:00–15:20 | Completed, 20 minutes
[136] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 12-12: The service consisted of medication evaluation and management, including symptom review and medication counseling. No separately documented psychotherapy was provided.
[137] BH-D003, signed_treatment_plan_jan05.txt, lines 6-6: Episode dates: 2026-01-05 through 2026-01-30
[138] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: A therapy day is a calendar day on which Rowan participates in individual, group, or family psychotherapy. Patient-present individual, group, and family therapy contribute to the minute goal. Medication management, contacts with collateral informants only, and care coordination do not contribute. This is the program's individualized treatment-plan goal for Rowan.
[139] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: Local treatment participation goal: at least 3 therapy days and at least 150 minutes of patient-present therapy in each Monday–Sunday week.
[140] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: at least 150 minutes of patient-present therapy
[141] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: at least 3 therapy days

Task 2: weekly; patients Rowan Mercer.

Snapshot: 1. Question: How many therapy minutes and hours did Rowan actually receive during the review period, overall and for each Monday–Sunday week? Show calculations or supporting detail, and report any conclusion the available documents do not settle.

Review window: 2026-01-05 through 2026-01-30, inclusive.

Therapy minutes: **585 or 595** (**9.750 or 9.917 hours**, rounded to 3 decimals).

Monday-Sunday weekly calculations use the review-range contributions below. Thresholds are the documented goals; partial weeks are not silently prorated.

| Calendar week | Reviewed dates | Days | Minutes | Hours | Goal | Decision | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-01-05 to 2026-01-11 | 2026-01-05 to 2026-01-11 | 3 | 140 | 2.333 | 3 days and 150 minutes | not_met | [1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12], [13], [14], [97], [98], [99], [100], [15], [16], [17], [18], [19], [20], [21], [22], [137], [138], [139], [140], [141] |
| 2026-01-12 to 2026-01-18 | 2026-01-12 to 2026-01-18 | 2 | 120 | 2.000 | 3 days and 150 minutes | not_met | [23], [24], [25], [26], [27], [28], [29], [30], [101], [102], [103], [104], [105], [31], [32], [33], [106], [107], [108], [109], [110], [111], [112], [113], [114], [115], [116], [137], [138], [139], [140], [141] |
| 2026-01-19 to 2026-01-25 | 2026-01-19 to 2026-01-25 | 3 | 180 | 3.000 | 3 days and 150 minutes | met | [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56], [57], [58], [59], [60], [61], [62], [63], [64], [65], [66], [67], [68], [69], [70], [71], [72], [73], [117], [118], [119], [120], [121], [137], [138], [139], [140], [141] |
| 2026-01-26 to 2026-02-01 | 2026-01-26 to 2026-01-30 | 3 | 145 or 155 | 2.417 or 2.583 | 3 days and 150 minutes | cannot be determined | [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87], [122], [123], [124], [125], [126], [127], [128], [129], [130], [131], [132], [133], [69], [88], [70], [71], [89], [90], [91], [92], [93], [94], [95], [96], [134], [135], [136], [137], [138], [139], [140], [141] |

Calculation ledger:

| Date | Encounter | Service | Included | Contact minutes | Reason | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-01-05 | HG-E101 | individual | included | 50 | Eligible attended patient therapy under the effective plan. | [1], [2], [3], [4], [5] |
| 2026-01-06 | HG-E102 | group | included | 45 | Eligible attended patient therapy under the effective plan. | [6], [7], [8], [9], [10], [11], [12], [13], [14] |
| 2026-01-08 | HG-E103 | individual | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [97], [98], [99], [100] |
| 2026-01-09 | HG-E104 | family | included | 45 | Eligible attended patient therapy under the effective plan. | [15], [16], [17], [18], [19], [20], [21], [22] |
| 2026-01-12 | HG-E105 | group | included | 75 | Eligible attended patient therapy under the effective plan. | [23], [24], [25], [26], [27], [28], [29], [30] |
| 2026-01-13 | HG-E106 | medication | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [101], [102], [103], [104], [105] |
| 2026-01-14 | HG-E107 | individual | included | 45 | Eligible attended patient therapy under the effective plan. | [31], [32], [33] |
| 2026-01-15 | HG-E108 | group | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [106], [107], [108], [109] |
| 2026-01-16 | HG-E109 | collateral | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [110], [111], [112], [113], [114], [115], [116] |
| 2026-01-19 | HG-E110 | group | included | 60 | Eligible attended patient therapy under the effective plan. | [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56] |
| 2026-01-19 | HG-E111 | individual | included | 30 | Eligible attended patient therapy under the effective plan. | [57], [58], [59], [60], [61] |
| 2026-01-21 | HG-E112 | individual | included | 45 | Eligible attended patient therapy under the effective plan. | [62], [63], [64], [65], [66], [67] |
| 2026-01-22 | HG-E113 | group | included | 45 | Eligible attended patient therapy under the effective plan. | [68], [69], [70], [71], [72], [73] |
| 2026-01-23 | HG-E114 | coordination | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [117], [118], [119], [120], [121] |
| 2026-01-26 | HG-E115 | individual | included | 40 or 50 | Eligible attended patient therapy under the effective plan. | [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87] |
| 2026-01-27 | HG-E116 | group | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [122], [123], [124], [125], [126], [127], [128], [129], [130], [131] |
| 2026-01-28 | HG-E117 | individual | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [132], [133] |
| 2026-01-29 | HG-E118 | group | included | 75 | Eligible attended patient therapy under the effective plan. | [69], [88], [70], [71], [89], [90] |
| 2026-01-30 | HG-E119 | family | included | 30 | Eligible attended patient therapy under the effective plan. | [91], [92], [93], [94], [95], [96] |
| 2026-01-30 | HG-E120 | medication | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [134], [135], [136] |

Supported event interpretations below are alternatives for the same encounter, rather than additional visits. Dates, service types, attendance, and durations within each interpretation stay together.

- HG-E115, alternative 1: 2026-01-26, individual, attended, patient present yes, 40 minutes; eligible yes, within review window yes; choices event:HG-E115=0, event:harbor grove behavioral health::HG-M042:HG-E115=2026-01-26:individual:attended:True:40. [80], [81], [82], [83], [84], [85], [86], [87]
- HG-E115, alternative 2: 2026-01-26, individual, attended, patient present yes, 50 minutes; eligible yes, within review window yes; choices event:HG-E115=1, event:harbor grove behavioral health::HG-M042:HG-E115=2026-01-26:individual:attended:True:50. [74], [75], [76], [77], [78], [79]

Reconciliation decisions:

- HG-E101, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [1], [2], [3], [4], [5]
- HG-E101, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [1], [2], [3], [4]
- HG-E102, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [6], [7], [8], [9], [10], [11], [12], [13], [14]
- HG-E102, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [6], [7], [8], [9], [10], [11], [12], [13]
- HG-E103, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [97], [98], [99], [100]
- HG-E103, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [97], [98], [99], [100]
- HG-E104, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [15], [16], [17], [18], [19], [20], [21], [22]
- HG-E104, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [16], [17], [18], [19], [20], [21], [22]
- HG-E105, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [23], [24], [25], [26], [27], [28], [29], [30]
- HG-E105, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [23], [24], [25], [27], [28], [29], [30]
- HG-E106, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [101], [102], [103], [104], [105]
- HG-E106, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [102], [103], [104], [105]
- HG-E107, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [31], [32], [33]
- HG-E107, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [32], [33]
- HG-E108, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [106], [107], [108], [109]
- HG-E108, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [106], [107], [108], [109]
- HG-E109, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [110], [111], [112], [113], [114], [115], [116]
- HG-E109, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [112], [113], [114], [115], [116]
- HG-E110, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56]
- HG-E110, departure (established): Apply the scoped correction to matching fields, not receipt order. [50], [51], [52]
- HG-E110, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56]
- HG-E111, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [57], [58], [59], [60], [61]
- HG-E111, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [57], [58], [59], [60], [61]
- HG-E112, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [62], [63], [64], [65], [66], [67]
- HG-E112, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [62], [63], [64], [65], [66], [67]
- HG-E113, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [68], [69], [70], [71], [72], [73]
- HG-E113, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [68], [69], [70], [71], [72], [73]
- HG-E114, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [117], [118], [119], [120], [121]
- HG-E114, duration (missing_evidence): Intersect attendance with activity and remove breaks for each interpretation. [117], [118], [119], [120], [121]
- HG-E115, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87]
- HG-E115, duration (conflicting_evidence): Intersect attendance with activity and remove breaks for each interpretation. [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87]
- HG-E116, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [122], [123], [124], [125], [126], [127], [128], [129], [130], [131]
- HG-E116, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [122], [123]
- HG-E117, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [132], [133]
- HG-E117, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [132], [133]
- HG-E118, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [69], [88], [70], [71], [89], [90]
- HG-E118, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [69], [88], [70], [71], [89], [90]
- HG-E119, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [91], [92], [93], [94], [95], [96]
- HG-E119, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [91], [92], [93], [94], [95], [96]
- HG-E120, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [134], [135], [136]
- HG-E120, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [134], [135], [136]


Unresolved conclusions and limitations:

- 2026-01-05 to 2026-01-30, therapy minutes: Values are discrete alternatives from consistent source interpretations.
- Week of 2026-01-26: Supported interpretations disagree, duration is missing, or week coverage is incomplete.

Additional evidence needed:

- patient harbor grove behavioral health::HG-M042, HG-E115, 2026-01-05 through 2026-01-30, duration: Supported records disagree on actual patient-contact duration: 40 or 50 minutes. Obtain an explicit duration correction scoped to patient harbor grove behavioral health::HG-M042, encounter HG-E115, 2026-01-26, identifying which earlier assertion it replaces, or the actual patient-contact start/end times and break record for that encounter. [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87]

Source passages:

[1] BH-D002, intake_and_individual_jan05.txt, lines 6-6: Encounter HG-E101 | Service date 2026-01-05
[2] BH-D002, intake_and_individual_jan05.txt, lines 8-8: Patient-present individual therapy: 09:00–09:50 local; completed, 50 minutes.
[3] BH-D002, intake_and_individual_jan05.txt, lines 8-8: completed, 50 minutes.
[4] BH-D002, intake_and_individual_jan05.txt, lines 13-13: Rowan arrived independently and participated throughout the appointment.
[5] BH-D006, early_appointment_status_export.txt, lines 10-10: HG-E101   | Jan05 | Individual therapy     | 09:00–09:50    | Completed
[6] BH-D004, group_facilitator_jan06.txt, lines 5-5: Service date 2026-01-06 | Group scheduled 10:00–11:30 local
[7] BH-D004, group_facilitator_jan06.txt, lines 7-7: Facilitator: Leena Park, LPC
[8] BH-D004, group_facilitator_jan06.txt, lines 12-12: The whole group took a break from 10:45 to 11:00. No therapy was conducted during that interval.
[9] BH-D004, group_facilitator_jan06.txt, lines 14-14: The patient attendance roster is maintained by the group desk.
[10] BH-D005, early_group_attendance_roster.txt, lines 10-10: 2026-01-06 | HG-E102   | 10:00–11:30    | 10:15           | 11:15            | Attended part
[11] BH-D005, early_group_attendance_roster.txt, lines 13-13: Departure was marked when Rowan returned their visitor badge. Rowan did not re-enter the group room after departing.
[12] BH-D005, early_group_attendance_roster.txt, lines 13-13: Rowan advised the facilitator that they would need to leave early for a previously arranged ride.
[13] BH-D005, early_group_attendance_roster.txt, lines 13-13: Rowan called from the building entrance to say they were running behind after difficulty finding parking.
[14] BH-D006, early_appointment_status_export.txt, lines 11-11: HG-E102   | Jan06 | Coping skills group    | 10:00–11:30    | Attended part
[15] BH-D006, early_appointment_status_export.txt, lines 13-13: HG-E104   | Jan09 | Family therapy         | 14:00–14:45    | Completed
[16] BH-D007, family_primary_jan09.txt, lines 6-6: Encounter HG-E104 | 2026-01-09, 14:00–14:45 local
[17] BH-D007, family_primary_jan09.txt, lines 7-7: Present: Rowan and partner, Casey Mercer
[18] BH-D007, family_primary_jan09.txt, lines 9-9: Patient-present family therapy duration: 45 minutes
[19] BH-D007, family_primary_jan09.txt, lines 10-10: Mara Voss signed 2026-01-09, 16:24 local
[20] BH-D008, family_cofacilitator_jan09.txt, lines 6-6: Encounter HG-E104 | Date 2026-01-09 | 14:00–14:45 local
[21] BH-D008, family_cofacilitator_jan09.txt, lines 8-8: Participants: Rowan Mercer and Casey Mercer; both present for the full 45 minutes
[22] BH-D008, family_cofacilitator_jan09.txt, lines 8-8: both present for the full 45 minutes
[23] BH-D005, early_group_attendance_roster.txt, lines 11-11: 2026-01-12 | HG-E105   | 10:00–11:30    | 10:00           | 11:30            | Attended full
[24] BH-D005, early_group_attendance_roster.txt, lines 15-15: No transport concern was reported at that time.
[25] BH-D005, early_group_attendance_roster.txt, lines 15-15: Rowan checked in before the group began and remained until the group was released.
[26] BH-D006, early_appointment_status_export.txt, lines 14-14: HG-E105   | Jan12 | Coping skills group    | 10:00–11:30    | Completed
[27] BH-D009, group_facilitator_jan12.txt, lines 6-6: Service date 2026-01-12 | Scheduled group 10:00–11:30 local
[28] BH-D009, group_facilitator_jan12.txt, lines 7-7: Facilitator: Leena Park, LPC
[29] BH-D009, group_facilitator_jan12.txt, lines 12-12: Group break: 10:40–10:55; no therapeutic activity occurred during the break.
[30] BH-D009, group_facilitator_jan12.txt, lines 16-16: Attendance is recorded on the group desk roster.
[31] BH-D006, early_appointment_status_export.txt, lines 16-16: HG-E107   | Jan14 | Individual therapy     | 11:00–11:45    | Completed
[32] BH-D011, individual_therapy_jan14.txt, lines 6-6: Encounter HG-E107 | Date 2026-01-14
[33] BH-D011, individual_therapy_jan14.txt, lines 7-7: Patient-present session 11:00–11:45 local; completed, 45 minutes
[34] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 3-3: Skills group clinical record | Service date: January 19, 2026
[35] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 4-4: Group encounter: HG-E110 | Facilitator: Leah Chen, LCSW
[36] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 5-5: Patient chart: Rowan Mercer | DOB: 1991-04-12 | MRN: HG-M042
[37] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 6-6: Scheduled group: 10:00–11:30. Nontherapeutic break: 10:45–11:00.
[38] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 8-8: The break was for restroom use and refreshments; there was no facilitated discussion, assigned therapeutic activity, or patient treatment during that interval.
[39] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 10-10: Patient-specific arrival and departure are maintained on the attendance roster.
[40] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 4-4: Service date: January 19, 2026 | Group encounter: HG-E110
[41] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 5-5: Patient: Rowan Mercer | DOB: 1991-04-12 | MRN: HG-M042
[42] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 8-8: Scheduled opening: 10:00 | Scheduled closing: 11:30
[43] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 9-9: Patient arrival: 10:00 | Patient departure: 11:30 | Status: Attended
[44] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 10-10: Roster disposition: Final, signed
[45] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 12-12: This is the patient row from the facilitator's attendance sheet.
[46] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 16-16: The staff member closing the roster certified the patient row as shown at the time of signing.
[47] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 16-16: This roster is the original signed attendance entry for the listed service date.
[48] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 18-18: Electronically signed: Leah Chen, LCSW | January 19, 2026, 12:14
[49] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 19-19: Document status: Final
[50] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 7-7: Correction: Patient departure for HG-E110 is 11:15, replacing the original roster value of 11:30. Patient arrival remains 10:00.
[51] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 11-11: The original signed roster is retained in the chart with this correction attached to its attendance entry.
[52] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 11-11: This correction applies only to Rowan Mercer's departure field on the January 19 group attendance roster. It does not change the group service date, scheduled opening or closing, the break recorded in the group clinical note, or the separate individual appointment.
[53] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 11-11: Service date: January 19, 2026 | Group encounter: HG-E110
[54] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 13-13: Scheduled opening: 10:00 | Scheduled closing: 11:30
[55] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 14-14: Patient arrival: 10:00 | Patient departure: 11:30 | Status: Attended
[56] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 20-20: This is a retransmission of the January 19 roster for HG-E110. The received copy contains no new clinician signature and records no additional visit.
[57] BH-D105, BH-D105_individual_2026-01-19.txt, lines 3-3: Individual psychotherapy | Encounter HG-E111
[58] BH-D105, BH-D105_individual_2026-01-19.txt, lines 5-5: January 19, 2026 | In person
[59] BH-D105, BH-D105_individual_2026-01-19.txt, lines 6-6: Completed: 30 minutes
[60] BH-D105, BH-D105_individual_2026-01-19.txt, lines 6-6: Patient contact: 11:15–11:45 | Completed: 30 minutes
[61] BH-D105, BH-D105_individual_2026-01-19.txt, lines 11-11: Rowan participated throughout the individual contact
[62] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Connection was lost from 13:20–13:30; there was no therapeutic contact during that interval.
[63] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Patient contact occurred 13:00–13:20 and 13:30–13:55.
[64] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: The reconnection continued the same clinical encounter under original appointment HG-A112.
[65] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Total patient psychotherapy contact: 45 minutes.
[66] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 15-15: ATTACHED PLATFORM CONNECTION EXPORT
[67] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 16-18: Appointment ID | Call ID | Connected | Ended HG-A112 | VC-112A | January 21 13:00 | January 21 13:20 HG-A112 | VC-112B | January 21 13:30 | January 21 13:55
[68] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 7-7: January 22, 2026 | Encounter HG-E113
[69] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 8-8: Scheduled group 10:00–11:30. Nontherapeutic break 10:45–11:00.
[70] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 13-13: Scheduled group 10:00–11:30. Nontherapeutic break 10:45–11:00.
[71] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 17-17: For both dates, the break was unstructured time without therapeutic activity or facilitator treatment. Patient arrival, departure, and attendance status are entered in the separate attendance register.
[72] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 9-9: January 22 | HG-E113 | Skills group | 10:00–11:30 | 10:30 | 11:30 | Attended, late arrival
[73] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 14-14: January 22 attendance attestation: Rowan arrived at 10:30 and remained until the group closed. Signed: Leah Chen, LCSW, January 22, 12:09.
[74] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 3-3: Individual psychotherapy | Encounter HG-E115 | Appointment HG-A115
[75] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 5-5: January 26, 2026 | In person
[76] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 6-6: Clinicians: Mira Patel, LCSW; Nora Ellis, LCSW
[77] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 7-7: Actual patient psychotherapy contact: 09:00–09:50, 50 minutes.
[78] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 15-15: Electronically signed: Mira Patel, LCSW | January 26, 2026, 11:16
[79] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 16-16: Record status: Final
[80] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 4-4: Encounter HG-E115 | Appointment HG-A115 | Service date January 26, 2026
[81] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 6-6: Service: Individual psychotherapy, in person
[82] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 7-7: Actual patient psychotherapy contact: 09:10–09:50, 40 minutes.
[83] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 10-10: Rowan entered the treatment room at 09:10, when we began the session.
[84] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 10-10: The full patient-contact interval for the encounter was 09:10–09:50.
[85] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 14-14: The session concluded with Rowan at 09:50.
[86] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 16-16: Electronically signed: Nora Ellis, LCSW | January 26, 2026, 12:03
[87] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 17-17: Record status: Final
[88] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 12-12: January 29, 2026 | Encounter HG-E118
[89] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 12-12: January 29 | HG-E118 | Skills group | 10:00–11:30 | 10:00 | 11:30 | Attended
[90] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 20-20: January 29 attendance attestation: Rowan was present from opening through closing. Signed: Leah Chen, LCSW, January 29, 12:15.
[91] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 3-3: Family psychotherapy | Encounter HG-E119
[92] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 5-5: January 30, 2026 | In person | Clinician: Mira Patel, LCSW
[93] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 6-6: Therapist session interval: 13:00–13:45, 45 minutes.
[94] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 7-7: Partner only: 13:00–13:15. Rowan present with partner: 13:15–13:45, 30 minutes.
[95] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 7-7: Rowan present with partner: 13:15–13:45, 30 minutes.
[96] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 11-11: Rowan joined at 13:15 and participated through the end of the session.
[97] BH-D006, early_appointment_status_export.txt, lines 12-12: HG-E103   | Jan08 | Individual therapy     | 11:00–11:45    | No show
[98] BH-D006, early_appointment_status_export.txt, lines 20-20: HG-E103 remained unarrived at close of its appointment slot on January 8.
[99] BH-D015, missed_visit_outreach_jan08.txt, lines 6-6: Related appointment: HG-E103, 2026-01-08, 11:00–11:45 local
[100] BH-D015, missed_visit_outreach_jan08.txt, lines 11-11: 11:45: Appointment marked no show. Rowan was not seen for the scheduled individual visit.
[101] BH-D006, early_appointment_status_export.txt, lines 15-15: HG-E106   | Jan13 | Medication management  | 09:00–09:25    | Completed
[102] BH-D010, medication_review_jan13.txt, lines 6-6: Encounter HG-E106 | Date 2026-01-13
[103] BH-D010, medication_review_jan13.txt, lines 7-7: Actual visit 09:00–09:25 local; completed, 25 minutes
[104] BH-D010, medication_review_jan13.txt, lines 11-11: Rowan attended for medication management.
[105] BH-D010, medication_review_jan13.txt, lines 17-17: Service documented: medication review and management only. No separate psychotherapy component was provided or documented.
[106] BH-D006, early_appointment_status_export.txt, lines 17-17: HG-E108   | Jan15 | Coping skills group    | 10:00–11:30    | Clinic cancelled
[107] BH-D006, early_appointment_status_export.txt, lines 20-20: HG-E108 was removed from the active room schedule after staff illness was reported. A cancellation message was released to all registered members.
[108] BH-D016, group_cancellation_notice_jan15.txt, lines 9-9: The coping skills group scheduled for January 15 from 10:00 to 11:30 is cancelled by the clinic because of staff illness.
[109] BH-D016, group_cancellation_notice_jan15.txt, lines 15-15: No group was held and no participants were seen for HG-E108.
[110] BH-D006, early_appointment_status_export.txt, lines 18-18: HG-E109   | Jan16 | Family collateral      | 14:00–14:40    | Completed
[111] BH-D006, early_appointment_status_export.txt, lines 20-20: Appointment HG-E109 was retained as a partner collateral contact after Rowan could not attend.
[112] BH-D012, partner_collateral_jan16.txt, lines 6-6: Encounter HG-E109 | Date 2026-01-16 | 14:00–14:40 local
[113] BH-D012, partner_collateral_jan16.txt, lines 8-8: Participant: Casey Mercer, partner. Rowan was absent for the entire contact.
[114] BH-D012, partner_collateral_jan16.txt, lines 11-11: Casey attended the arranged contact after Rowan advised the office that they could not participate.
[115] BH-D012, partner_collateral_jan16.txt, lines 11-11: This was a collateral discussion with Casey only, focused on observations at home and ways to support the treatment plan.
[116] BH-D012, partner_collateral_jan16.txt, lines 17-17: Rowan did not join in person, by telephone, or by video. No patient-present psychotherapy occurred during this contact.
[117] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 3-3: Care coordination | Encounter HG-E114
[118] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 5-5: January 23, 2026 | 09:00–09:20
[119] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 6-6: Participants: Mira Patel, LCSW, and Daniel Shaw, outside social worker
[120] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 7-7: Patient participation: None. No patient contact occurred.
[121] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 13-13: This contact was between professionals only. Rowan did not join by telephone or video, and no psychotherapy was delivered to the patient during the call.
[122] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 10-10: January 27 | HG-E116 | Skills group | 10:00–11:30 | — | — | No show; patient did not attend
[123] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 16-16: January 27 attendance attestation: Final roster confirms Rowan was absent for the entire group. No patient treatment contact occurred. An outreach message inviting the patient to contact scheduling was left after the group; no clinical discussion occurred. Signed: Leah Chen, LCSW, January 27, 11:54.
[124] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 9-9: Status: DRAFT — UNSIGNED — system populated from scheduled group template
[125] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 10-10: Scheduled service: Skills group, 10:00–11:30
[126] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 11-11: Template attendance text: Patient attended the full session and participated in the skills discussion.
[127] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 18-18: SECTION B — POSTED CHARGE EXTRACT
[128] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 20-20: Service date: January 27, 2026
[129] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 21-21: Description: Group psychotherapy
[130] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 22-22: Quantity charged: 1 group session
[131] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 23-23: Charge status in this export: Posted
[132] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 11-11: January 28 | HG-E117 | Individual | 14:00–14:45 | — | — | Patient cancelled before appointment
[133] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 18-18: January 28 scheduling entry: Cancellation received from patient January 28, 08:12. Rowan reported a personal scheduling conflict. Appointment HG-E117 was cancelled before the scheduled start; no replacement appointment was booked within January 2026. Entered by Ana Reed, January 28, 08:18.
[134] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 5-5: Completed, 20 minutes
[135] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 5-5: January 30, 2026 | 15:00–15:20 | Completed, 20 minutes
[136] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 12-12: The service consisted of medication evaluation and management, including symptom review and medication counseling. No separately documented psychotherapy was provided.
[137] BH-D003, signed_treatment_plan_jan05.txt, lines 6-6: Episode dates: 2026-01-05 through 2026-01-30
[138] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: A therapy day is a calendar day on which Rowan participates in individual, group, or family psychotherapy. Patient-present individual, group, and family therapy contribute to the minute goal. Medication management, contacts with collateral informants only, and care coordination do not contribute. This is the program's individualized treatment-plan goal for Rowan.
[139] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: Local treatment participation goal: at least 3 therapy days and at least 150 minutes of patient-present therapy in each Monday–Sunday week.
[140] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: at least 150 minutes of patient-present therapy
[141] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: at least 3 therapy days

## DEV-03

Snapshot: 1. Question: For each week, did the delivered therapy meet the goal documented in Rowan’s treatment plan? State the goal, the relevant therapy-day and minute totals, and whether it was met, not met, or cannot be determined from the current record.

Review window: 2026-01-05 through 2026-01-30, inclusive.

Eligible sessions: **12**. Distinct therapy days: **11**. Therapy minutes: **585 or 595** (**9.750 or 9.917 hours**, rounded to 3 decimals).

Monday-Sunday weekly calculations use the review-range contributions below. Thresholds are the documented goals; partial weeks are not silently prorated.

| Calendar week | Reviewed dates | Days | Minutes | Hours | Goal | Decision | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-01-05 to 2026-01-11 | 2026-01-05 to 2026-01-11 | 3 | 140 | 2.333 | 3 days and 150 minutes | not_met | [1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12], [13], [14], [97], [98], [99], [100], [15], [16], [17], [18], [19], [20], [21], [22], [137], [138], [139], [140], [141] |
| 2026-01-12 to 2026-01-18 | 2026-01-12 to 2026-01-18 | 2 | 120 | 2.000 | 3 days and 150 minutes | not_met | [23], [24], [25], [26], [27], [28], [29], [30], [101], [102], [103], [104], [105], [31], [32], [33], [106], [107], [108], [109], [110], [111], [112], [113], [114], [115], [116], [137], [138], [139], [140], [141] |
| 2026-01-19 to 2026-01-25 | 2026-01-19 to 2026-01-25 | 3 | 180 | 3.000 | 3 days and 150 minutes | met | [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56], [57], [58], [59], [60], [61], [62], [63], [64], [65], [66], [67], [68], [69], [70], [71], [72], [73], [117], [118], [119], [120], [121], [137], [138], [139], [140], [141] |
| 2026-01-26 to 2026-02-01 | 2026-01-26 to 2026-01-30 | 3 | 145 or 155 | 2.417 or 2.583 | 3 days and 150 minutes | cannot be determined | [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87], [122], [123], [124], [125], [126], [127], [128], [129], [130], [131], [132], [133], [69], [88], [70], [71], [89], [90], [91], [92], [93], [94], [95], [96], [134], [135], [136], [137], [138], [139], [140], [141] |

Calculation ledger:

| Date | Encounter | Service | Included | Contact minutes | Reason | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-01-05 | HG-E101 | individual | included | 50 | Eligible attended patient therapy under the effective plan. | [1], [2], [3], [4], [5] |
| 2026-01-06 | HG-E102 | group | included | 45 | Eligible attended patient therapy under the effective plan. | [6], [7], [8], [9], [10], [11], [12], [13], [14] |
| 2026-01-08 | HG-E103 | individual | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [97], [98], [99], [100] |
| 2026-01-09 | HG-E104 | family | included | 45 | Eligible attended patient therapy under the effective plan. | [15], [16], [17], [18], [19], [20], [21], [22] |
| 2026-01-12 | HG-E105 | group | included | 75 | Eligible attended patient therapy under the effective plan. | [23], [24], [25], [26], [27], [28], [29], [30] |
| 2026-01-13 | HG-E106 | medication | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [101], [102], [103], [104], [105] |
| 2026-01-14 | HG-E107 | individual | included | 45 | Eligible attended patient therapy under the effective plan. | [31], [32], [33] |
| 2026-01-15 | HG-E108 | group | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [106], [107], [108], [109] |
| 2026-01-16 | HG-E109 | collateral | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [110], [111], [112], [113], [114], [115], [116] |
| 2026-01-19 | HG-E110 | group | included | 60 | Eligible attended patient therapy under the effective plan. | [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56] |
| 2026-01-19 | HG-E111 | individual | included | 30 | Eligible attended patient therapy under the effective plan. | [57], [58], [59], [60], [61] |
| 2026-01-21 | HG-E112 | individual | included | 45 | Eligible attended patient therapy under the effective plan. | [62], [63], [64], [65], [66], [67] |
| 2026-01-22 | HG-E113 | group | included | 45 | Eligible attended patient therapy under the effective plan. | [68], [69], [70], [71], [72], [73] |
| 2026-01-23 | HG-E114 | coordination | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [117], [118], [119], [120], [121] |
| 2026-01-26 | HG-E115 | individual | included | 40 or 50 | Eligible attended patient therapy under the effective plan. | [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87] |
| 2026-01-27 | HG-E116 | group | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [122], [123], [124], [125], [126], [127], [128], [129], [130], [131] |
| 2026-01-28 | HG-E117 | individual | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [132], [133] |
| 2026-01-29 | HG-E118 | group | included | 75 | Eligible attended patient therapy under the effective plan. | [69], [88], [70], [71], [89], [90] |
| 2026-01-30 | HG-E119 | family | included | 30 | Eligible attended patient therapy under the effective plan. | [91], [92], [93], [94], [95], [96] |
| 2026-01-30 | HG-E120 | medication | excluded | 0 counted | Every event interpretation is absent or excluded by the effective plan. | [134], [135], [136] |

Supported event interpretations below are alternatives for the same encounter, rather than additional visits. Dates, service types, attendance, and durations within each interpretation stay together.

- HG-E115, alternative 1: 2026-01-26, individual, attended, patient present yes, 40 minutes; eligible yes, within review window yes; choices event:HG-E115=0, event:harbor grove behavioral health::HG-M042:HG-E115=2026-01-26:individual:attended:True:40. [80], [81], [82], [83], [84], [85], [86], [87]
- HG-E115, alternative 2: 2026-01-26, individual, attended, patient present yes, 50 minutes; eligible yes, within review window yes; choices event:HG-E115=1, event:harbor grove behavioral health::HG-M042:HG-E115=2026-01-26:individual:attended:True:50. [74], [75], [76], [77], [78], [79]

Reconciliation decisions:

- HG-E101, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [1], [2], [3], [4], [5]
- HG-E101, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [1], [2], [3], [4]
- HG-E102, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [6], [7], [8], [9], [10], [11], [12], [13], [14]
- HG-E102, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [6], [7], [8], [9], [10], [11], [12], [13]
- HG-E103, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [97], [98], [99], [100]
- HG-E103, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [97], [98], [99], [100]
- HG-E104, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [15], [16], [17], [18], [19], [20], [21], [22]
- HG-E104, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [16], [17], [18], [19], [20], [21], [22]
- HG-E105, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [23], [24], [25], [26], [27], [28], [29], [30]
- HG-E105, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [23], [24], [25], [27], [28], [29], [30]
- HG-E106, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [101], [102], [103], [104], [105]
- HG-E106, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [102], [103], [104], [105]
- HG-E107, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [31], [32], [33]
- HG-E107, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [32], [33]
- HG-E108, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [106], [107], [108], [109]
- HG-E108, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [106], [107], [108], [109]
- HG-E109, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [110], [111], [112], [113], [114], [115], [116]
- HG-E109, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [112], [113], [114], [115], [116]
- HG-E110, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56]
- HG-E110, departure (established): Apply the scoped correction to matching fields, not receipt order. [50], [51], [52]
- HG-E110, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55], [56]
- HG-E111, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [57], [58], [59], [60], [61]
- HG-E111, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [57], [58], [59], [60], [61]
- HG-E112, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [62], [63], [64], [65], [66], [67]
- HG-E112, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [62], [63], [64], [65], [66], [67]
- HG-E113, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [68], [69], [70], [71], [72], [73]
- HG-E113, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [68], [69], [70], [71], [72], [73]
- HG-E114, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [117], [118], [119], [120], [121]
- HG-E114, duration (missing_evidence): Intersect attendance with activity and remove breaks for each interpretation. [117], [118], [119], [120], [121]
- HG-E115, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87]
- HG-E115, duration (conflicting_evidence): Intersect attendance with activity and remove breaks for each interpretation. [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87]
- HG-E116, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [122], [123], [124], [125], [126], [127], [128], [129], [130], [131]
- HG-E116, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [122], [123]
- HG-E117, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [132], [133]
- HG-E117, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [132], [133]
- HG-E118, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [69], [88], [70], [71], [89], [90]
- HG-E118, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [69], [88], [70], [71], [89], [90]
- HG-E119, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [91], [92], [93], [94], [95], [96]
- HG-E119, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [91], [92], [93], [94], [95], [96]
- HG-E120, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [134], [135], [136]
- HG-E120, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [134], [135], [136]


Unresolved conclusions and limitations:

- 2026-01-05 to 2026-01-30, therapy minutes: Values are discrete alternatives from consistent source interpretations.
- Week of 2026-01-26: Supported interpretations disagree, duration is missing, or week coverage is incomplete.

Additional evidence needed:

- patient harbor grove behavioral health::HG-M042, HG-E115, 2026-01-05 through 2026-01-30, duration: Supported records disagree on actual patient-contact duration: 40 or 50 minutes. Obtain an explicit duration correction scoped to patient harbor grove behavioral health::HG-M042, encounter HG-E115, 2026-01-26, identifying which earlier assertion it replaces, or the actual patient-contact start/end times and break record for that encounter. [74], [75], [76], [77], [78], [79], [80], [81], [82], [83], [84], [85], [86], [87]

Source passages:

[1] BH-D002, intake_and_individual_jan05.txt, lines 6-6: Encounter HG-E101 | Service date 2026-01-05
[2] BH-D002, intake_and_individual_jan05.txt, lines 8-8: Patient-present individual therapy: 09:00–09:50 local; completed, 50 minutes.
[3] BH-D002, intake_and_individual_jan05.txt, lines 8-8: completed, 50 minutes.
[4] BH-D002, intake_and_individual_jan05.txt, lines 13-13: Rowan arrived independently and participated throughout the appointment.
[5] BH-D006, early_appointment_status_export.txt, lines 10-10: HG-E101   | Jan05 | Individual therapy     | 09:00–09:50    | Completed
[6] BH-D004, group_facilitator_jan06.txt, lines 5-5: Service date 2026-01-06 | Group scheduled 10:00–11:30 local
[7] BH-D004, group_facilitator_jan06.txt, lines 7-7: Facilitator: Leena Park, LPC
[8] BH-D004, group_facilitator_jan06.txt, lines 12-12: The whole group took a break from 10:45 to 11:00. No therapy was conducted during that interval.
[9] BH-D004, group_facilitator_jan06.txt, lines 14-14: The patient attendance roster is maintained by the group desk.
[10] BH-D005, early_group_attendance_roster.txt, lines 10-10: 2026-01-06 | HG-E102   | 10:00–11:30    | 10:15           | 11:15            | Attended part
[11] BH-D005, early_group_attendance_roster.txt, lines 13-13: Departure was marked when Rowan returned their visitor badge. Rowan did not re-enter the group room after departing.
[12] BH-D005, early_group_attendance_roster.txt, lines 13-13: Rowan advised the facilitator that they would need to leave early for a previously arranged ride.
[13] BH-D005, early_group_attendance_roster.txt, lines 13-13: Rowan called from the building entrance to say they were running behind after difficulty finding parking.
[14] BH-D006, early_appointment_status_export.txt, lines 11-11: HG-E102   | Jan06 | Coping skills group    | 10:00–11:30    | Attended part
[15] BH-D006, early_appointment_status_export.txt, lines 13-13: HG-E104   | Jan09 | Family therapy         | 14:00–14:45    | Completed
[16] BH-D007, family_primary_jan09.txt, lines 6-6: Encounter HG-E104 | 2026-01-09, 14:00–14:45 local
[17] BH-D007, family_primary_jan09.txt, lines 7-7: Present: Rowan and partner, Casey Mercer
[18] BH-D007, family_primary_jan09.txt, lines 9-9: Patient-present family therapy duration: 45 minutes
[19] BH-D007, family_primary_jan09.txt, lines 10-10: Mara Voss signed 2026-01-09, 16:24 local
[20] BH-D008, family_cofacilitator_jan09.txt, lines 6-6: Encounter HG-E104 | Date 2026-01-09 | 14:00–14:45 local
[21] BH-D008, family_cofacilitator_jan09.txt, lines 8-8: Participants: Rowan Mercer and Casey Mercer; both present for the full 45 minutes
[22] BH-D008, family_cofacilitator_jan09.txt, lines 8-8: both present for the full 45 minutes
[23] BH-D005, early_group_attendance_roster.txt, lines 11-11: 2026-01-12 | HG-E105   | 10:00–11:30    | 10:00           | 11:30            | Attended full
[24] BH-D005, early_group_attendance_roster.txt, lines 15-15: No transport concern was reported at that time.
[25] BH-D005, early_group_attendance_roster.txt, lines 15-15: Rowan checked in before the group began and remained until the group was released.
[26] BH-D006, early_appointment_status_export.txt, lines 14-14: HG-E105   | Jan12 | Coping skills group    | 10:00–11:30    | Completed
[27] BH-D009, group_facilitator_jan12.txt, lines 6-6: Service date 2026-01-12 | Scheduled group 10:00–11:30 local
[28] BH-D009, group_facilitator_jan12.txt, lines 7-7: Facilitator: Leena Park, LPC
[29] BH-D009, group_facilitator_jan12.txt, lines 12-12: Group break: 10:40–10:55; no therapeutic activity occurred during the break.
[30] BH-D009, group_facilitator_jan12.txt, lines 16-16: Attendance is recorded on the group desk roster.
[31] BH-D006, early_appointment_status_export.txt, lines 16-16: HG-E107   | Jan14 | Individual therapy     | 11:00–11:45    | Completed
[32] BH-D011, individual_therapy_jan14.txt, lines 6-6: Encounter HG-E107 | Date 2026-01-14
[33] BH-D011, individual_therapy_jan14.txt, lines 7-7: Patient-present session 11:00–11:45 local; completed, 45 minutes
[34] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 3-3: Skills group clinical record | Service date: January 19, 2026
[35] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 4-4: Group encounter: HG-E110 | Facilitator: Leah Chen, LCSW
[36] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 5-5: Patient chart: Rowan Mercer | DOB: 1991-04-12 | MRN: HG-M042
[37] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 6-6: Scheduled group: 10:00–11:30. Nontherapeutic break: 10:45–11:00.
[38] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 8-8: The break was for restroom use and refreshments; there was no facilitated discussion, assigned therapeutic activity, or patient treatment during that interval.
[39] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 10-10: Patient-specific arrival and departure are maintained on the attendance roster.
[40] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 4-4: Service date: January 19, 2026 | Group encounter: HG-E110
[41] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 5-5: Patient: Rowan Mercer | DOB: 1991-04-12 | MRN: HG-M042
[42] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 8-8: Scheduled opening: 10:00 | Scheduled closing: 11:30
[43] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 9-9: Patient arrival: 10:00 | Patient departure: 11:30 | Status: Attended
[44] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 10-10: Roster disposition: Final, signed
[45] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 12-12: This is the patient row from the facilitator's attendance sheet.
[46] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 16-16: The staff member closing the roster certified the patient row as shown at the time of signing.
[47] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 16-16: This roster is the original signed attendance entry for the listed service date.
[48] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 18-18: Electronically signed: Leah Chen, LCSW | January 19, 2026, 12:14
[49] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 19-19: Document status: Final
[50] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 7-7: Correction: Patient departure for HG-E110 is 11:15, replacing the original roster value of 11:30. Patient arrival remains 10:00.
[51] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 11-11: The original signed roster is retained in the chart with this correction attached to its attendance entry.
[52] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 11-11: This correction applies only to Rowan Mercer's departure field on the January 19 group attendance roster. It does not change the group service date, scheduled opening or closing, the break recorded in the group clinical note, or the separate individual appointment.
[53] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 11-11: Service date: January 19, 2026 | Group encounter: HG-E110
[54] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 13-13: Scheduled opening: 10:00 | Scheduled closing: 11:30
[55] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 14-14: Patient arrival: 10:00 | Patient departure: 11:30 | Status: Attended
[56] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 20-20: This is a retransmission of the January 19 roster for HG-E110. The received copy contains no new clinician signature and records no additional visit.
[57] BH-D105, BH-D105_individual_2026-01-19.txt, lines 3-3: Individual psychotherapy | Encounter HG-E111
[58] BH-D105, BH-D105_individual_2026-01-19.txt, lines 5-5: January 19, 2026 | In person
[59] BH-D105, BH-D105_individual_2026-01-19.txt, lines 6-6: Completed: 30 minutes
[60] BH-D105, BH-D105_individual_2026-01-19.txt, lines 6-6: Patient contact: 11:15–11:45 | Completed: 30 minutes
[61] BH-D105, BH-D105_individual_2026-01-19.txt, lines 11-11: Rowan participated throughout the individual contact
[62] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Connection was lost from 13:20–13:30; there was no therapeutic contact during that interval.
[63] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Patient contact occurred 13:00–13:20 and 13:30–13:55.
[64] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: The reconnection continued the same clinical encounter under original appointment HG-A112.
[65] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Total patient psychotherapy contact: 45 minutes.
[66] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 15-15: ATTACHED PLATFORM CONNECTION EXPORT
[67] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 16-18: Appointment ID | Call ID | Connected | Ended HG-A112 | VC-112A | January 21 13:00 | January 21 13:20 HG-A112 | VC-112B | January 21 13:30 | January 21 13:55
[68] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 7-7: January 22, 2026 | Encounter HG-E113
[69] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 8-8: Scheduled group 10:00–11:30. Nontherapeutic break 10:45–11:00.
[70] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 13-13: Scheduled group 10:00–11:30. Nontherapeutic break 10:45–11:00.
[71] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 17-17: For both dates, the break was unstructured time without therapeutic activity or facilitator treatment. Patient arrival, departure, and attendance status are entered in the separate attendance register.
[72] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 9-9: January 22 | HG-E113 | Skills group | 10:00–11:30 | 10:30 | 11:30 | Attended, late arrival
[73] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 14-14: January 22 attendance attestation: Rowan arrived at 10:30 and remained until the group closed. Signed: Leah Chen, LCSW, January 22, 12:09.
[74] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 3-3: Individual psychotherapy | Encounter HG-E115 | Appointment HG-A115
[75] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 5-5: January 26, 2026 | In person
[76] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 6-6: Clinicians: Mira Patel, LCSW; Nora Ellis, LCSW
[77] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 7-7: Actual patient psychotherapy contact: 09:00–09:50, 50 minutes.
[78] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 15-15: Electronically signed: Mira Patel, LCSW | January 26, 2026, 11:16
[79] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 16-16: Record status: Final
[80] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 4-4: Encounter HG-E115 | Appointment HG-A115 | Service date January 26, 2026
[81] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 6-6: Service: Individual psychotherapy, in person
[82] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 7-7: Actual patient psychotherapy contact: 09:10–09:50, 40 minutes.
[83] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 10-10: Rowan entered the treatment room at 09:10, when we began the session.
[84] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 10-10: The full patient-contact interval for the encounter was 09:10–09:50.
[85] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 14-14: The session concluded with Rowan at 09:50.
[86] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 16-16: Electronically signed: Nora Ellis, LCSW | January 26, 2026, 12:03
[87] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 17-17: Record status: Final
[88] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 12-12: January 29, 2026 | Encounter HG-E118
[89] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 12-12: January 29 | HG-E118 | Skills group | 10:00–11:30 | 10:00 | 11:30 | Attended
[90] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 20-20: January 29 attendance attestation: Rowan was present from opening through closing. Signed: Leah Chen, LCSW, January 29, 12:15.
[91] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 3-3: Family psychotherapy | Encounter HG-E119
[92] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 5-5: January 30, 2026 | In person | Clinician: Mira Patel, LCSW
[93] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 6-6: Therapist session interval: 13:00–13:45, 45 minutes.
[94] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 7-7: Partner only: 13:00–13:15. Rowan present with partner: 13:15–13:45, 30 minutes.
[95] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 7-7: Rowan present with partner: 13:15–13:45, 30 minutes.
[96] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 11-11: Rowan joined at 13:15 and participated through the end of the session.
[97] BH-D006, early_appointment_status_export.txt, lines 12-12: HG-E103   | Jan08 | Individual therapy     | 11:00–11:45    | No show
[98] BH-D006, early_appointment_status_export.txt, lines 20-20: HG-E103 remained unarrived at close of its appointment slot on January 8.
[99] BH-D015, missed_visit_outreach_jan08.txt, lines 6-6: Related appointment: HG-E103, 2026-01-08, 11:00–11:45 local
[100] BH-D015, missed_visit_outreach_jan08.txt, lines 11-11: 11:45: Appointment marked no show. Rowan was not seen for the scheduled individual visit.
[101] BH-D006, early_appointment_status_export.txt, lines 15-15: HG-E106   | Jan13 | Medication management  | 09:00–09:25    | Completed
[102] BH-D010, medication_review_jan13.txt, lines 6-6: Encounter HG-E106 | Date 2026-01-13
[103] BH-D010, medication_review_jan13.txt, lines 7-7: Actual visit 09:00–09:25 local; completed, 25 minutes
[104] BH-D010, medication_review_jan13.txt, lines 11-11: Rowan attended for medication management.
[105] BH-D010, medication_review_jan13.txt, lines 17-17: Service documented: medication review and management only. No separate psychotherapy component was provided or documented.
[106] BH-D006, early_appointment_status_export.txt, lines 17-17: HG-E108   | Jan15 | Coping skills group    | 10:00–11:30    | Clinic cancelled
[107] BH-D006, early_appointment_status_export.txt, lines 20-20: HG-E108 was removed from the active room schedule after staff illness was reported. A cancellation message was released to all registered members.
[108] BH-D016, group_cancellation_notice_jan15.txt, lines 9-9: The coping skills group scheduled for January 15 from 10:00 to 11:30 is cancelled by the clinic because of staff illness.
[109] BH-D016, group_cancellation_notice_jan15.txt, lines 15-15: No group was held and no participants were seen for HG-E108.
[110] BH-D006, early_appointment_status_export.txt, lines 18-18: HG-E109   | Jan16 | Family collateral      | 14:00–14:40    | Completed
[111] BH-D006, early_appointment_status_export.txt, lines 20-20: Appointment HG-E109 was retained as a partner collateral contact after Rowan could not attend.
[112] BH-D012, partner_collateral_jan16.txt, lines 6-6: Encounter HG-E109 | Date 2026-01-16 | 14:00–14:40 local
[113] BH-D012, partner_collateral_jan16.txt, lines 8-8: Participant: Casey Mercer, partner. Rowan was absent for the entire contact.
[114] BH-D012, partner_collateral_jan16.txt, lines 11-11: Casey attended the arranged contact after Rowan advised the office that they could not participate.
[115] BH-D012, partner_collateral_jan16.txt, lines 11-11: This was a collateral discussion with Casey only, focused on observations at home and ways to support the treatment plan.
[116] BH-D012, partner_collateral_jan16.txt, lines 17-17: Rowan did not join in person, by telephone, or by video. No patient-present psychotherapy occurred during this contact.
[117] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 3-3: Care coordination | Encounter HG-E114
[118] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 5-5: January 23, 2026 | 09:00–09:20
[119] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 6-6: Participants: Mira Patel, LCSW, and Daniel Shaw, outside social worker
[120] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 7-7: Patient participation: None. No patient contact occurred.
[121] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 13-13: This contact was between professionals only. Rowan did not join by telephone or video, and no psychotherapy was delivered to the patient during the call.
[122] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 10-10: January 27 | HG-E116 | Skills group | 10:00–11:30 | — | — | No show; patient did not attend
[123] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 16-16: January 27 attendance attestation: Final roster confirms Rowan was absent for the entire group. No patient treatment contact occurred. An outreach message inviting the patient to contact scheduling was left after the group; no clinical discussion occurred. Signed: Leah Chen, LCSW, January 27, 11:54.
[124] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 9-9: Status: DRAFT — UNSIGNED — system populated from scheduled group template
[125] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 10-10: Scheduled service: Skills group, 10:00–11:30
[126] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 11-11: Template attendance text: Patient attended the full session and participated in the skills discussion.
[127] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 18-18: SECTION B — POSTED CHARGE EXTRACT
[128] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 20-20: Service date: January 27, 2026
[129] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 21-21: Description: Group psychotherapy
[130] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 22-22: Quantity charged: 1 group session
[131] BH-D112, BH-D112_draft_note_and_charge_extract_2026-01-27.txt, lines 23-23: Charge status in this export: Posted
[132] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 11-11: January 28 | HG-E117 | Individual | 14:00–14:45 | — | — | Patient cancelled before appointment
[133] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 18-18: January 28 scheduling entry: Cancellation received from patient January 28, 08:12. Rowan reported a personal scheduling conflict. Appointment HG-E117 was cancelled before the scheduled start; no replacement appointment was booked within January 2026. Entered by Ana Reed, January 28, 08:18.
[134] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 5-5: Completed, 20 minutes
[135] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 5-5: January 30, 2026 | 15:00–15:20 | Completed, 20 minutes
[136] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 12-12: The service consisted of medication evaluation and management, including symptom review and medication counseling. No separately documented psychotherapy was provided.
[137] BH-D003, signed_treatment_plan_jan05.txt, lines 6-6: Episode dates: 2026-01-05 through 2026-01-30
[138] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: A therapy day is a calendar day on which Rowan participates in individual, group, or family psychotherapy. Patient-present individual, group, and family therapy contribute to the minute goal. Medication management, contacts with collateral informants only, and care coordination do not contribute. This is the program's individualized treatment-plan goal for Rowan.
[139] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: Local treatment participation goal: at least 3 therapy days and at least 150 minutes of patient-present therapy in each Monday–Sunday week.
[140] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: at least 150 minutes of patient-present therapy
[141] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: at least 3 therapy days

## DEV-04

Snapshot: 1. Question: Reconstruct the care on January 19 and January 21. How many therapy contacts and patient therapy minutes occurred on each date, and how do the attendance records, clinical notes, later documents, and telehealth records affect your answer?

Review window: 2026-01-19 through 2026-01-19, inclusive.

Eligible sessions: **2**. Therapy minutes: **90** (**1.500 hours**, rounded to 3 decimals).

Monday-Sunday weekly calculations use the review-range contributions below. Thresholds are the documented goals; partial weeks are not silently prorated.

| Calendar week | Reviewed dates | Days | Minutes | Hours | Goal | Decision | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-01-19 to 2026-01-25 | 2026-01-19 to 2026-01-19 | 1 | 90 | 1.500 | 3 days and 150 minutes | cannot be determined | [23], [24], [25], [26], [27], [28], [29], [30], [31], [32], [33], [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45], [46], [47], [48], [49], [50], [51], [52], [53], [54], [55] |

Calculation ledger:

| Date | Encounter | Service | Included | Contact minutes | Reason | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-01-19 | HG-E110 | group | included | 60 | Eligible attended patient therapy under the effective plan. | [23], [24], [25], [26], [27], [28], [29], [30], [31], [32], [33], [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45] |
| 2026-01-19 | HG-E111 | individual | included | 30 | Eligible attended patient therapy under the effective plan. | [46], [47], [48], [49], [50] |

Review window: 2026-01-21 through 2026-01-21, inclusive.

Eligible sessions: **1**. Therapy minutes: **45** (**0.750 hours**, rounded to 3 decimals).

Monday-Sunday weekly calculations use the review-range contributions below. Thresholds are the documented goals; partial weeks are not silently prorated.

| Calendar week | Reviewed dates | Days | Minutes | Hours | Goal | Decision | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-01-19 to 2026-01-25 | 2026-01-21 to 2026-01-21 | 1 | 45 | 0.750 | 3 days and 150 minutes | cannot be determined | [56], [57], [58], [59], [60], [61], [51], [52], [53], [54], [55] |

Calculation ledger:

| Date | Encounter | Service | Included | Contact minutes | Reason | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-01-21 | HG-E112 | individual | included | 45 | Eligible attended patient therapy under the effective plan. | [56], [57], [58], [59], [60], [61] |

Reconciliation decisions:

- HG-E110, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [23], [24], [25], [26], [27], [28], [29], [30], [31], [32], [33], [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45]
- HG-E110, departure (established): Apply the scoped correction to matching fields, not receipt order. [39], [40], [41]
- HG-E110, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [23], [24], [25], [26], [27], [28], [29], [30], [31], [32], [33], [34], [35], [36], [37], [38], [39], [40], [41], [42], [43], [44], [45]
- HG-E111, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [46], [47], [48], [49], [50]
- HG-E111, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [46], [47], [48], [49], [50]
- HG-E112, attendance (established): Patient-specific disposition establishes attendance; drafts add no visit. [56], [57], [58], [59], [60], [61]
- HG-E112, duration (established): Intersect attendance with activity and remove breaks for each interpretation. [56], [57], [58], [59], [60], [61]

- 2026-01-19, clinician observation: Rowan became visibly tense and stated the group discussion felt difficult to manage when the topic turned to returning to the workplace. [1]
- 2026-01-19, clinician observation: Rowan attended the opening check-in, accepted the exercise handout, and requested additional help from the individual clinician. [2]
- 2026-01-19, clinician observation: Work-related task was narrowed to drafting two sentences to a supervisor, with discussion of tolerating an incomplete draft. [3]
- 2026-01-19, clinician observation: Rowan denied suicidal thoughts, remained future oriented, and no acute safety concern was identified. [4]
- 2026-01-19, clinician observation: Persistent avoidance and disrupted sleep continue to interfere with resuming usual work routine. [5]
- 2026-01-19, patient report: Rowan reported postponing a message to a supervisor as a familiar avoidance pattern. [6]
- 2026-01-19, patient report: The patient identified anxiety about reconnecting with work. [7]
- 2026-01-19, patient report: Rowan reported feeling overwhelmed by workplace discussions and worried about difficulties keeping up if returning to work. [8]
- 2026-01-19, patient report: Rowan identified muscle tension, rapid breathing, and urge to leave as early signs of anxiety activation. [9]
- 2026-01-19, patient report: Rowan reported anxiety intensity eased enough to discuss a next step. [10]
- 2026-01-19, reason for contact: A same-day individual meeting was arranged due to Rowan's difficulty managing the group discussion about returning to the workplace. [11]
- 2026-01-19, reason for contact: Rowan requested additional help, leading staff to arrange access to the individual clinician. [12]
- 2026-01-19, reason for contact: Visit added due to anxiety during group requiring individual grounding and coping review. [13]
- 2026-01-21, clinician observation: Explored Rowan's uncertainty about the supervisor's response versus evidence for a negative response. [14]
- 2026-01-21, clinician observation: Rowan was engaged and able to restate the agreed task. [15]
- 2026-01-21, clinician observation: No urgent safety concern was reported. [16]
- 2026-01-21, patient report: Rowan reported drafting a message about returning to work but did not send it, checked the draft repeatedly, and practiced reading it and planning to send it. [17], [18], [19]
- 2026-01-21, patient report: Rowan described one night of improved sleep and another of prolonged wakefulness; discussed evening routines. [20], [21], [22]

Unresolved conclusions and limitations:

- Week of 2026-01-19: Supported interpretations disagree, duration is missing, or week coverage is incomplete.

Source passages:

[1] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 10-10: When discussion turned to returning to the workplace, Rowan became visibly tense and said the amount of discussion felt difficult to manage.
[2] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 18-18: Rowan attended the opening check-in, accepted the exercise handout, and requested additional help from the individual clinician.
[3] BH-D105, BH-D105_individual_2026-01-19.txt, lines 11-11: We narrowed the work-related task to drafting two sentences to a supervisor, without requiring that the message be sent today. Discussed allowing an incomplete draft to exist rather than abandoning the task because the wording felt imperfect.
[4] BH-D105, BH-D105_individual_2026-01-19.txt, lines 13-13: Rowan denied current suicidal thoughts and remained future oriented in discussing the next appointment. No acute safety concern was identified during this contact.
[5] BH-D105, BH-D105_individual_2026-01-19.txt, lines 13-13: Persistent avoidance and disrupted sleep continue to interfere with resuming a usual work routine.
[6] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 10-10: Rowan initially followed the exercise and identified postponing a message to a supervisor as a familiar pattern.
[7] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 14-14: Rowan was present for the opening check-in. The patient identified anxiety about reconnecting with work and accepted an exercise handout.
[8] BH-D105, BH-D105_individual_2026-01-19.txt, lines 9-9: The patient described feeling overwhelmed when other members discussed workplace demands and worried that returning to work would expose difficulties keeping up.
[9] BH-D105, BH-D105_individual_2026-01-19.txt, lines 9-9: Rowan was able to identify muscle tension, rapid breathing, and an urge to leave as early signs of activation.
[10] BH-D105, BH-D105_individual_2026-01-19.txt, lines 11-11: Rowan participated throughout the individual contact and reported that the immediate intensity of anxiety eased enough to discuss a next step.
[11] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 10-10: The facilitator offered grounding and arranged a same-day individual meeting with the treating clinician.
[12] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 14-14: Staff arranged access to the individual clinician after Rowan requested additional help.
[13] BH-D105, BH-D105_individual_2026-01-19.txt, lines 9-9: This visit was added because Rowan became anxious during group and needed individual grounding and review of coping strategies.
[14] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 9-9: Explored the difference between uncertainty about the supervisor's response and evidence that a response would be negative.
[15] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 11-11: Rowan was engaged and able to restate the agreed task.
[16] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 11-11: No urgent safety concern was reported.
[17] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 9-9: Practiced reading the draft once and choosing a planned time to send it.
[18] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 9-9: Rowan reported drafting a short message about a possible gradual return to work but stopping before sending it.
[19] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 9-9: The patient identified checking the draft repeatedly as another way the task was being delayed.
[20] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 11-11: After the connection resumed, the discussion returned to the same task and to evening routines.
[21] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 11-11: Discussed keeping the wind-down routine brief and repeatable.
[22] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 11-11: Rowan described one night of improved sleep followed by a night of prolonged wakefulness.
[23] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 3-3: Skills group clinical record | Service date: January 19, 2026
[24] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 4-4: Group encounter: HG-E110 | Facilitator: Leah Chen, LCSW
[25] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 5-5: Patient chart: Rowan Mercer | DOB: 1991-04-12 | MRN: HG-M042
[26] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 6-6: Scheduled group: 10:00–11:30. Nontherapeutic break: 10:45–11:00.
[27] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 8-8: The break was for restroom use and refreshments; there was no facilitated discussion, assigned therapeutic activity, or patient treatment during that interval.
[28] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 10-10: Patient-specific arrival and departure are maintained on the attendance roster.
[29] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 4-4: Service date: January 19, 2026 | Group encounter: HG-E110
[30] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 5-5: Patient: Rowan Mercer | DOB: 1991-04-12 | MRN: HG-M042
[31] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 8-8: Scheduled opening: 10:00 | Scheduled closing: 11:30
[32] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 9-9: Patient arrival: 10:00 | Patient departure: 11:30 | Status: Attended
[33] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 10-10: Roster disposition: Final, signed
[34] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 12-12: This is the patient row from the facilitator's attendance sheet.
[35] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 16-16: The staff member closing the roster certified the patient row as shown at the time of signing.
[36] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 16-16: This roster is the original signed attendance entry for the listed service date.
[37] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 18-18: Electronically signed: Leah Chen, LCSW | January 19, 2026, 12:14
[38] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 19-19: Document status: Final
[39] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 7-7: Correction: Patient departure for HG-E110 is 11:15, replacing the original roster value of 11:30. Patient arrival remains 10:00.
[40] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 11-11: The original signed roster is retained in the chart with this correction attached to its attendance entry.
[41] BH-D103, BH-D103_attendance_correction_2026-01-20.txt, lines 11-11: This correction applies only to Rowan Mercer's departure field on the January 19 group attendance roster. It does not change the group service date, scheduled opening or closing, the break recorded in the group clinical note, or the separate individual appointment.
[42] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 11-11: Service date: January 19, 2026 | Group encounter: HG-E110
[43] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 13-13: Scheduled opening: 10:00 | Scheduled closing: 11:30
[44] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 14-14: Patient arrival: 10:00 | Patient departure: 11:30 | Status: Attended
[45] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 20-20: This is a retransmission of the January 19 roster for HG-E110. The received copy contains no new clinician signature and records no additional visit.
[46] BH-D105, BH-D105_individual_2026-01-19.txt, lines 3-3: Individual psychotherapy | Encounter HG-E111
[47] BH-D105, BH-D105_individual_2026-01-19.txt, lines 5-5: January 19, 2026 | In person
[48] BH-D105, BH-D105_individual_2026-01-19.txt, lines 6-6: Completed: 30 minutes
[49] BH-D105, BH-D105_individual_2026-01-19.txt, lines 6-6: Patient contact: 11:15–11:45 | Completed: 30 minutes
[50] BH-D105, BH-D105_individual_2026-01-19.txt, lines 11-11: Rowan participated throughout the individual contact
[51] BH-D003, signed_treatment_plan_jan05.txt, lines 6-6: Episode dates: 2026-01-05 through 2026-01-30
[52] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: A therapy day is a calendar day on which Rowan participates in individual, group, or family psychotherapy. Patient-present individual, group, and family therapy contribute to the minute goal. Medication management, contacts with collateral informants only, and care coordination do not contribute. This is the program's individualized treatment-plan goal for Rowan.
[53] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: Local treatment participation goal: at least 3 therapy days and at least 150 minutes of patient-present therapy in each Monday–Sunday week.
[54] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: at least 150 minutes of patient-present therapy
[55] BH-D003, signed_treatment_plan_jan05.txt, lines 12-12: at least 3 therapy days
[56] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Connection was lost from 13:20–13:30; there was no therapeutic contact during that interval.
[57] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Patient contact occurred 13:00–13:20 and 13:30–13:55.
[58] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: The reconnection continued the same clinical encounter under original appointment HG-A112.
[59] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 7-7: Total patient psychotherapy contact: 45 minutes.
[60] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 15-15: ATTACHED PLATFORM CONNECTION EXPORT
[61] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 16-18: Appointment ID | Call ID | Connected | Ended HG-A112 | VC-112A | January 21 13:00 | January 21 13:20 HG-A112 | VC-112B | January 21 13:30 | January 21 13:55

## DEV-05

Snapshot: 1. Question: Summarize the documented symptom course during the episode and the reason for the additional individual contact on January 19. Which symptom assessments are distinct, and what conclusions about progress can and cannot be supported?

The processed record contains **3 distinct symptom assessments** in the requested period. Completion dates identify measurements; later imports and reviews are provenance rather than additional measurements.

| Completed | Instrument | Score | Item 9 | Form | Period membership | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-01-05 | PHQ-9 | 18 | not documented | not documented | established | [1], [2] |
| 2026-01-16 | PHQ-9 | 14 | not documented | HG-Q116 | established | [3], [4], [5], [6], [7] |
| 2026-01-30 | PHQ-9 | 10 | 0 | not documented | established | [8], [9] |

PHQ-9: 18 on 2026-01-05 to 10 on 2026-01-30; numerical change -8. [1], [2], [8], [9]

Attributed clinical course:

Patient reports:

- 2026-01-05: Rowan reports low mood, reduced interest, fragmented sleep, difficulty starting tasks, increased worry about returning to work, postponing emails, avoiding conversations about return date, and spending more time alone. [19], [20], [21]
- 2026-01-05: Rowan reports waking in the night and repeatedly checking the time. [22]
- 2026-01-05: Rowan selected opening work inbox for five minutes as a task step. [23]
- 2026-01-05: Rowan reported depressed mood, sleep disruption, anxiety about resuming work responsibilities, and avoidance of tasks and communication. [24]
- 2026-01-05: Rowan expressed a desire to improve follow-through even if anxiety persists. [25]
- 2026-01-06: Patient reported running behind after difficulty finding parking. [29]
- 2026-01-06: Patient reported needing to leave early for a previously arranged ride. [30]
- 2026-01-06: Rowan reported delaying a reply to a work message due to fear of being asked for a firm return date. [31]
- 2026-01-08: Rowan reported missing the appointment after a poor night of sleep. [33]
- 2026-01-09: Rowan reported experiencing partner reminders as evidence of falling behind. [42]
- 2026-01-09: Rowan reported that an evening walk felt more acceptable than a lengthy review of unfinished tasks. [43]
- 2026-01-09: Rowan reported feeling watched when repeatedly asked about contacting work. [44]
- 2026-01-12: Patient reported no transport concern. [47]
- 2026-01-12: Rowan reported difficulty opening work messages and identified looking at one message as a more manageable step than replying to all. [48]
- 2026-01-12: Rowan reported that taking a walk with Casey helped reduce evening worry. [49]
- 2026-01-12: Rowan planned to attempt an action after breakfast and expressed concern about coping if the morning went poorly. [50]
- 2026-01-13: Rowan reported continuing sleep interruption and daytime tiredness. [52]
- 2026-01-13: Mood is somewhat less heavy on days with a planned activity but Rowan remains concerned about work communication. [53]
- 2026-01-14: Rowan reported completing several small activities, including opening a work message and taking two short walks. [55]
- 2026-01-14: Rowan has not yet replied to the work message and continues to imagine being asked questions they cannot answer. [56]
- 2026-01-14: Rowan described the family appointment as helpful because the planned check-in with Casey reduced repeated reminders. [57]
- 2026-01-14: Sleep remains interrupted, and getting started in the morning continues to require effort. [58]
- 2026-01-14: Rowan noticed physical tension during the rehearsal but was able to remain with the task. [59]
- 2026-01-14: Rowan identified setting out appointment information the evening before as a helpful preparation step. [60]
- 2026-01-15: Rowan acknowledged receiving the cancellation notice and did not request changes to remaining appointments. [61]
- 2026-01-16: Getting out of the apartment has become a little easier, but thinking about work continues to lead to avoidance. [70]
- 2026-01-16: Sleep is inconsistent. [71]
- 2026-01-19: Rowan reported postponing a message to a supervisor as a familiar avoidance pattern. [77]
- 2026-01-19: The patient identified anxiety about reconnecting with work. [78]
- 2026-01-19: Rowan reported feeling overwhelmed by workplace discussions and worried about difficulties keeping up if returning to work. [79]
- 2026-01-19: Rowan identified muscle tension, rapid breathing, and urge to leave as early signs of anxiety activation. [80]
- 2026-01-19: Rowan reported anxiety intensity eased enough to discuss a next step. [81]
- 2026-01-21: Rowan reported drafting a message about returning to work but did not send it, checked the draft repeatedly, and practiced reading it and planning to send it. [88], [89], [90]
- 2026-01-21: Rowan described one night of improved sleep and another of prolonged wakefulness; discussed evening routines. [91], [92], [93]
- 2026-01-22: Rowan used opening a work calendar as an example and described concern that seeing outstanding items would become overwhelming. [96]
- 2026-01-26: Rowan reported sending a message to the supervisor, feeling some uncertainty reduced, but also worrying about being asked for commitments and continued to postpone scheduling a conversation. [106]
- 2026-01-26: Rowan reported uneven sleep and difficulty settling at night due to repetitive work-related thoughts. [107]
- 2026-01-26: Rowan reported no current suicidal ideation. [108]
- 2026-01-26: Rowan reported difficulty transitioning from a supervisor's reply to arranging the next conversation and anticipated feeling overwhelmed if several work issues were raised at once. [109], [110]
- 2026-01-26: Rowan recognized a tendency to keep editing a message after the essential point was clear. [111]
- 2026-01-26: Rowan reported that repetitive planning at night affected settling for sleep. [112]
- 2026-01-26: Rowan described a wish to resume a steadier routine. [113]
- 2026-01-28: Rowan reported a personal scheduling conflict. [114]
- 2026-01-29: Rowan reported opening the work calendar but delaying a follow-up conversation. [116]
- 2026-01-30: Rowan reported ongoing anxiety about the work conversation but found a limited plan more manageable. [126]
- 2026-01-30: Patient reported adherence to medication and no new adverse effects. [127]
- 2026-01-30: Patient reported mood improvement but persistent anxiety related to work. [128]
- 2026-01-30: Patient reported variable sleep. [129]
- 2026-01-30: Patient denied current suicidal thoughts. [130]
- 2026-01-30: Patient reports ongoing sleep difficulty and trouble sustaining usual activities, with fewer days of pervasive low mood than at intake. [131]

Clinician observations:

- 2026-01-05: Clinician observed subdued but responsive affect, clear and organized speech, and noted that daytime fatigue increases avoidance. [10], [11], [12]
- 2026-01-05: No immediate safety concern identified; Rowan able to discuss support contacts and ways to seek help. [13]
- 2026-01-05: Clinician impression: depressive symptoms with anxiety and behavioral avoidance. [14]
- 2026-01-05: Rowan has difficulty with daily activity and task initiation; the team will focus on completion of useful steps rather than mood. [15]
- 2026-01-05: Rowan experiences anxiety and disrupted sleep; will practice grounding or paced-breathing and establish a morning routine. [16]
- 2026-01-05: Rowan avoids communication related to employment; individual and family sessions will address gradual preparation and support. [17]
- 2026-01-06: Rowan practiced a breathing exercise and chose reading the message before responding as a next step. [27]
- 2026-01-06: Rowan's participation was relevant and they appeared receptive to peer suggestions. [28]
- 2026-01-08: Rowan Mercer did not arrive for the scheduled individual therapy appointment on January 8, 2026. [32]
- 2026-01-09: Clinician observed Rowan could articulate Casey's need for reassurance about preparation. [34]
- 2026-01-09: Clinician observed Casey could reflect Rowan's wish to maintain ownership of the return-to-work process. [35]
- 2026-01-09: Clinician observed that communication rehearsal became less defensive with repetition. [36]
- 2026-01-09: Rowan practiced asking for specific help and Casey practiced reflecting the request before offering suggestions. [37]
- 2026-01-09: Rowan was present and engaged, and described a shared evening walk as supportive and not pressuring. [38]
- 2026-01-09: Casey agreed to use a single planned check-in about work preparation, and Rowan agreed to communicate when they wanted practical assistance versus quiet company. [39]
- 2026-01-12: Patient remained for the full group session. [45]
- 2026-01-12: Rowan listened to peers and provided support to another group member. [46]
- 2026-01-13: Ongoing depressive and anxiety symptoms with sleep disruption. [51]
- 2026-01-14: Affect was more varied than at intake, although worry was evident when discussing employment. [54]
- 2026-01-16: Rowan Mercer was unable to attend the family collateral appointment on January 16, 2026. [62]
- 2026-01-16: Some improvement in depressive symptoms; ongoing avoidance of work communication and inconsistent sleep. [63]
- 2026-01-16: Persistent avoidance, difficulty initiating work communication, and sleep disruption remain clinically relevant. [64]
- 2026-01-16: Rowan has attempted small activities and communication practice but has not yet established a reliable routine. [65]
- 2026-01-19: Rowan became visibly tense and stated the group discussion felt difficult to manage when the topic turned to returning to the workplace. [72]
- 2026-01-19: Rowan attended the opening check-in, accepted the exercise handout, and requested additional help from the individual clinician. [73]
- 2026-01-19: Work-related task was narrowed to drafting two sentences to a supervisor, with discussion of tolerating an incomplete draft. [74]
- 2026-01-19: Rowan denied suicidal thoughts, remained future oriented, and no acute safety concern was identified. [75]
- 2026-01-19: Persistent avoidance and disrupted sleep continue to interfere with resuming usual work routine. [76]
- 2026-01-21: Explored Rowan's uncertainty about the supervisor's response versus evidence for a negative response. [85]
- 2026-01-21: Rowan was engaged and able to restate the agreed task. [86]
- 2026-01-21: No urgent safety concern was reported. [87]
- 2026-01-22: Facilitator encouraged Rowan to use a limited, planned review period and a stopping point. [94]
- 2026-01-22: Rowan contributed an example to the discussion after the break. [95]
- 2026-01-23: Current approach is to help Rowan break a difficult task into a manageable first step. [97]
- 2026-01-23: Avoidance and coping will continue to be addressed in scheduled therapy. [98]
- 2026-01-26: Rowan practiced responding to the supervisor's request, role-played communication, and with prompting was able to return to the main request; rehearsed a grounding cue. [100]
- 2026-01-26: Rowan was attentive and collaborative in session but hesitant to complete the task outside the office. [101]
- 2026-01-26: Ongoing work is focused on avoidance and improving the bedtime routine. [102]
- 2026-01-26: Plan to maintain scheduled treatment contact during return-to-work planning and bring the response draft to the next visit if needed. [103]
- 2026-01-26: Rowan could use a grounding cue during rehearsal but remained uncertain about using it independently when anxious. [104]
- 2026-01-26: Clinical presentation was consistent with ongoing anxiety, low mood, and functional difficulty around work demands. [105]
- 2026-01-29: Facilitator helped Rowan identify a specific question to ask and Rowan participated in rehearsal, accepting feedback about keeping the request brief. [115]
- 2026-01-30: A recurring pattern was identified: reminders about contacting work led to lengthy discussions and Rowan withdrawing from the task. [117]
- 2026-01-30: Rowan practiced requesting specific help and identifying when reminders felt overwhelming. [118]
- 2026-01-30: Patient was alert, organized, and able to describe the follow-up plan. [119]
- 2026-01-30: No new acute safety issue was observed. [120]
- 2026-01-30: Clinician observes partial improvement, but persistent avoidance and significant impact on returning to work. [121]
- 2026-01-30: Patient has taken initial steps (drafting and sending a message), but delays follow-up and becomes anxious with broader tasks. [122]
- 2026-01-30: Sleep disruption intermittently impedes establishing a steadier daytime routine. [123]
- 2026-01-30: Continued treatment is recommended due to ongoing difficulties with follow-through and work-related functioning. [124]

Collateral reports:

- 2026-01-05: Partner support is available, but repeated reminders sometimes increase tension. [18]
- 2026-01-09: Casey reported that reminders were intended to help but acknowledged that repeated prompts increased tension. [40]
- 2026-01-09: Casey reported worry that giving Rowan space might leave Rowan isolated. [41]
- 2026-01-16: Rowan had been getting out for short walks and seemed more willing to discuss the coming week. [66]
- 2026-01-16: Mornings remain difficult for Rowan, and Rowan becomes quiet when the conversation turns to work. [67]
- 2026-01-16: The scheduled evening check-in has reduced unplanned reminders for Rowan. [68]
- 2026-01-16: Casey has noticed less argument when asking what kind of help Rowan wants. [69]
- 2026-01-23: Rowan asked for help understanding whom to contact about a gradual return to work schedule. [99]
- 2026-01-30: Casey reported uncertainty about when reminders helped Rowan and when they increased Rowan's sense of pressure. [125]

Documented reasons for additional contact:

- 2026-01-05: Plan to participate in scheduled individual, group, and selected family appointments. [26]
- 2026-01-19: A same-day individual meeting was arranged due to Rowan's difficulty managing the group discussion about returning to the workplace. [82]
- 2026-01-19: Rowan requested additional help, leading staff to arrange access to the individual clinician. [83]
- 2026-01-19: Visit added due to anxiety during group requiring individual grounding and coping review. [84]


Score changes and the attributed observations above describe the documented course. They do not by themselves establish recovery, resolution of functional problems, or a causal effect of treatment. Missing measurements are not inferred.

Source passages:

[1] BH-D002, intake_and_individual_jan05.txt, lines 15-15: PHQ-9 completed by Rowan on 2026-01-05: total score 18.
[2] BH-D002, intake_and_individual_jan05.txt, lines 15-15: The questionnaire is retained in the assessment tab.
[3] BH-D013, symptom_measure_review_jan16.txt, lines 6-6: Instrument: PHQ-9 | Patient portal form HG-Q116
[4] BH-D013, symptom_measure_review_jan16.txt, lines 7-7: Completed by patient: 2026-01-16, 08:17 local
[5] BH-D013, symptom_measure_review_jan16.txt, lines 8-8: Total score: 14
[6] BH-D014, imported_measure_summary_received_jan26.txt, lines 12-13: Measure | Result | Date completed | Source form PHQ-9   | 14     | 2026-01-16     | HG-Q116
[7] BH-D014, imported_measure_summary_received_jan26.txt, lines 17-17: Import detail: copied result from the January 16 portal form. January 26 is the date the summary was received and filed. No newly completed patient questionnaire is included in this batch. The source form identifier and original completion date were retained in the imported row.
[8] BH-D115, BH-D115_symptom_measure_review_2026-01-30.txt, lines 5-5: Questionnaire completed January 30, 2026, 12:42
[9] BH-D115, BH-D115_symptom_measure_review_2026-01-30.txt, lines 6-6: PHQ-9 total: 10. Item 9: 0.
[10] BH-D002, intake_and_individual_jan05.txt, lines 13-13: Affect was subdued but responsive, especially when discussing their partner's support.
[11] BH-D002, intake_and_individual_jan05.txt, lines 13-13: Daytime fatigue appears to make avoidance more likely.
[12] BH-D002, intake_and_individual_jan05.txt, lines 13-13: Speech was clear and organized.
[13] BH-D002, intake_and_individual_jan05.txt, lines 13-13: No immediate safety concern was identified in today's assessment; Rowan was able to discuss support contacts and ways to seek additional help if needed.
[14] BH-D002, intake_and_individual_jan05.txt, lines 15-15: Clinical impressions are depressive symptoms with anxiety and behavioral avoidance.
[15] BH-D003, signed_treatment_plan_jan05.txt, lines 14-14: Goal 1: improve daily activity and task initiation. Rowan will select manageable activities, track attempts, and review barriers with the individual therapist. The team will emphasize completion of useful steps rather than judging the day by mood alone.
[16] BH-D003, signed_treatment_plan_jan05.txt, lines 16-16: Goal 2: improve coping with anxiety and disrupted sleep. Rowan will practice one grounding or paced-breathing exercise and establish a consistent morning routine. Group participation will provide opportunities to rehearse skills and hear alternative approaches.
[17] BH-D003, signed_treatment_plan_jan05.txt, lines 18-18: Goal 3: support a workable return to employment. Individual sessions will address avoided communication and gradual preparation. Family sessions may address how Rowan can request help and how the partner can offer support without taking over tasks.
[18] BH-D003, signed_treatment_plan_jan05.txt, lines 10-10: Partner support is available but repeated reminders sometimes increase tension.
[19] BH-D002, intake_and_individual_jan05.txt, lines 11-11: Rowan describes several weeks of low mood, reduced interest in usual activities, fragmented sleep, and difficulty beginning ordinary tasks.
[20] BH-D002, intake_and_individual_jan05.txt, lines 11-11: Rowan has been postponing email replies, avoiding conversations about the return date, and spending more time alone at home.
[21] BH-D002, intake_and_individual_jan05.txt, lines 11-11: Worry increases when thinking about returning to work after a recent leave.
[22] BH-D002, intake_and_individual_jan05.txt, lines 13-13: Rowan described waking in the night and then checking the time repeatedly.
[23] BH-D002, intake_and_individual_jan05.txt, lines 17-17: Rowan selected opening their work inbox for five minutes without requiring an immediate reply.
[24] BH-D003, signed_treatment_plan_jan05.txt, lines 10-10: Presenting needs: depressed mood, sleep disruption, anxiety about resuming work responsibilities, and avoidance of tasks and communication.
[25] BH-D003, signed_treatment_plan_jan05.txt, lines 10-10: Rowan wishes to improve follow-through without waiting for anxiety to disappear.
[26] BH-D002, intake_and_individual_jan05.txt, lines 19-19: Plan: participate in scheduled individual, group, and selected family appointments.
[27] BH-D004, group_facilitator_jan06.txt, lines 14-14: Rowan practiced a breathing exercise and selected reading the message before deciding how to respond as a possible next step.
[28] BH-D004, group_facilitator_jan06.txt, lines 14-14: Their participation was relevant to the topic, and they appeared receptive to peer suggestions.
[29] BH-D005, early_group_attendance_roster.txt, lines 13-13: Rowan called from the building entrance to say they were running behind after difficulty finding parking.
[30] BH-D005, early_group_attendance_roster.txt, lines 13-13: Rowan advised the facilitator that they would need to leave early for a previously arranged ride.
[31] BH-D004, group_facilitator_jan06.txt, lines 14-14: Rowan was quiet initially and responded when invited to identify a situation involving avoidance. They described delaying a reply to a work message because they feared being asked for a firm return date.
[32] BH-D006, early_appointment_status_export.txt, lines 20-20: HG-E103 remained unarrived at close of its appointment slot on January 8.
[33] BH-D015, missed_visit_outreach_jan08.txt, lines 15-15: They said the morning had gotten away from them after a poor night of sleep and confirmed that they still intended to attend the next day's visit with Casey.
[34] BH-D008, family_cofacilitator_jan09.txt, lines 13-13: Rowan was able to state that Casey wanted reassurance that some preparation was happening.
[35] BH-D008, family_cofacilitator_jan09.txt, lines 13-13: Casey reflected Rowan's wish to keep ownership of the return-to-work process.
[36] BH-D008, family_cofacilitator_jan09.txt, lines 13-13: The rehearsal became less defensive with repetition.
[37] BH-D007, family_primary_jan09.txt, lines 14-14: Rowan practiced asking for one specific kind of help, and Casey practiced reflecting the request before offering suggestions.
[38] BH-D007, family_primary_jan09.txt, lines 16-16: Rowan remained present and engaged throughout the visit. They became more animated when describing a shared evening walk and identified this as support that did not feel like pressure.
[39] BH-D007, family_primary_jan09.txt, lines 16-16: Casey agreed to use a single planned check-in about work preparation instead of repeated reminders. Rowan agreed to say when they wanted practical assistance versus quiet company.
[40] BH-D008, family_cofacilitator_jan09.txt, lines 11-11: Casey explained that the reminders were an attempt to help, while also recognizing that repeated prompts increased tension.
[41] BH-D007, family_primary_jan09.txt, lines 12-12: Casey described worry that giving Rowan space might leave them isolated.
[42] BH-D008, family_cofacilitator_jan09.txt, lines 11-11: Rowan initially described partner reminders as evidence that they were falling behind.
[43] BH-D008, family_cofacilitator_jan09.txt, lines 15-15: The couple selected an evening walk as an activity they could share without making it a discussion about progress. Rowan said this felt more acceptable than a lengthy review of unfinished tasks.
[44] BH-D007, family_primary_jan09.txt, lines 12-12: Rowan described feeling watched when asked repeatedly whether they had contacted work.
[45] BH-D005, early_group_attendance_roster.txt, lines 15-15: Rowan checked in before the group began and remained until the group was released.
[46] BH-D009, group_facilitator_jan12.txt, lines 16-16: Rowan listened to peers and offered a supportive comment to another member.
[47] BH-D005, early_group_attendance_roster.txt, lines 15-15: No transport concern was reported at that time.
[48] BH-D009, group_facilitator_jan12.txt, lines 14-14: Rowan contributed an example about leaving work messages unopened. They identified looking at one message as a lower step than replying to every outstanding message.
[49] BH-D009, group_facilitator_jan12.txt, lines 14-14: They also described taking a walk with Casey over the weekend and noted that it helped the evening feel less dominated by worry.
[50] BH-D009, group_facilitator_jan12.txt, lines 14-14: During the planning exercise, Rowan wrote down an action to try after breakfast and asked how to respond if the morning went poorly.
[51] BH-D010, medication_review_jan13.txt, lines 15-15: Assessment: ongoing depressive and anxiety symptoms with sleep disruption.
[52] BH-D010, medication_review_jan13.txt, lines 11-11: Rowan reported continuing sleep interruption and daytime tiredness.
[53] BH-D010, medication_review_jan13.txt, lines 11-11: They described mood as somewhat less heavy on days with a planned activity but remained concerned about work communication.
[54] BH-D011, individual_therapy_jan14.txt, lines 15-15: Affect was more varied than at intake, although worry was evident when discussing employment.
[55] BH-D011, individual_therapy_jan14.txt, lines 11-11: Rowan reported completing several small activities since the prior individual appointment, including opening a work message and taking two short walks.
[56] BH-D011, individual_therapy_jan14.txt, lines 11-11: They have not yet replied to the message and continue to imagine being asked questions they cannot answer.
[57] BH-D011, individual_therapy_jan14.txt, lines 11-11: Rowan described the family appointment as helpful because the planned check-in with Casey reduced repeated reminders.
[58] BH-D011, individual_therapy_jan14.txt, lines 11-11: Sleep remains interrupted, and getting started in the morning continues to require effort.
[59] BH-D011, individual_therapy_jan14.txt, lines 13-13: Rowan noticed physical tension during the rehearsal but was able to remain with the task.
[60] BH-D011, individual_therapy_jan14.txt, lines 15-15: Rowan identified setting out appointment information the evening before as a helpful preparation step.
[61] BH-D016, group_cancellation_notice_jan15.txt, lines 13-13: 08:37: Rowan called the desk and acknowledged receiving the notice. Staff confirmed that the family-related appointment on January 16 remained on the schedule and that later appointments would appear on the next weekly list. Rowan did not request a change to the remaining appointments during this call.
[62] BH-D006, early_appointment_status_export.txt, lines 20-20: Appointment HG-E109 was retained as a partner collateral contact after Rowan could not attend.
[63] BH-D014, imported_measure_summary_received_jan26.txt, lines 15-15: some improvement in depressive symptoms; ongoing avoidance of work communication and inconsistent sleep.
[64] BH-D013, symptom_measure_review_jan16.txt, lines 13-13: Persistent avoidance, difficulty initiating work communication, and sleep disruption remain clinically relevant.
[65] BH-D013, symptom_measure_review_jan16.txt, lines 13-13: Rowan has attempted small activities and communication practice but has not yet established a reliable routine.
[66] BH-D012, partner_collateral_jan16.txt, lines 13-13: Casey reported that Rowan had been getting out for short walks and seemed more willing to discuss the coming week.
[67] BH-D012, partner_collateral_jan16.txt, lines 13-13: Mornings remain difficult, and Casey described Rowan becoming quiet when the conversation turns to work.
[68] BH-D012, partner_collateral_jan16.txt, lines 13-13: The scheduled evening check-in has reduced unplanned reminders.
[69] BH-D012, partner_collateral_jan16.txt, lines 13-13: Casey said it takes effort to resist offering multiple solutions but has noticed less argument when asking what kind of help Rowan wants.
[70] BH-D013, symptom_measure_review_jan16.txt, lines 11-11: In the optional update field, Rowan wrote that getting out of the apartment had become a little easier, while thinking about work continued to make them want to put things off.
[71] BH-D013, symptom_measure_review_jan16.txt, lines 11-11: Rowan also described sleep as inconsistent.
[72] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 10-10: When discussion turned to returning to the workplace, Rowan became visibly tense and said the amount of discussion felt difficult to manage.
[73] BH-D104, BH-D104_resent_roster_received_2026-01-26.txt, lines 18-18: Rowan attended the opening check-in, accepted the exercise handout, and requested additional help from the individual clinician.
[74] BH-D105, BH-D105_individual_2026-01-19.txt, lines 11-11: We narrowed the work-related task to drafting two sentences to a supervisor, without requiring that the message be sent today. Discussed allowing an incomplete draft to exist rather than abandoning the task because the wording felt imperfect.
[75] BH-D105, BH-D105_individual_2026-01-19.txt, lines 13-13: Rowan denied current suicidal thoughts and remained future oriented in discussing the next appointment. No acute safety concern was identified during this contact.
[76] BH-D105, BH-D105_individual_2026-01-19.txt, lines 13-13: Persistent avoidance and disrupted sleep continue to interfere with resuming a usual work routine.
[77] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 10-10: Rowan initially followed the exercise and identified postponing a message to a supervisor as a familiar pattern.
[78] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 14-14: Rowan was present for the opening check-in. The patient identified anxiety about reconnecting with work and accepted an exercise handout.
[79] BH-D105, BH-D105_individual_2026-01-19.txt, lines 9-9: The patient described feeling overwhelmed when other members discussed workplace demands and worried that returning to work would expose difficulties keeping up.
[80] BH-D105, BH-D105_individual_2026-01-19.txt, lines 9-9: Rowan was able to identify muscle tension, rapid breathing, and an urge to leave as early signs of activation.
[81] BH-D105, BH-D105_individual_2026-01-19.txt, lines 11-11: Rowan participated throughout the individual contact and reported that the immediate intensity of anxiety eased enough to discuss a next step.
[82] BH-D101, BH-D101_group_content_2026-01-19.txt, lines 10-10: The facilitator offered grounding and arranged a same-day individual meeting with the treating clinician.
[83] BH-D102, BH-D102_original_attendance_2026-01-19.txt, lines 14-14: Staff arranged access to the individual clinician after Rowan requested additional help.
[84] BH-D105, BH-D105_individual_2026-01-19.txt, lines 9-9: This visit was added because Rowan became anxious during group and needed individual grounding and review of coping strategies.
[85] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 9-9: Explored the difference between uncertainty about the supervisor's response and evidence that a response would be negative.
[86] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 11-11: Rowan was engaged and able to restate the agreed task.
[87] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 11-11: No urgent safety concern was reported.
[88] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 9-9: Practiced reading the draft once and choosing a planned time to send it.
[89] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 9-9: Rowan reported drafting a short message about a possible gradual return to work but stopping before sending it.
[90] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 9-9: The patient identified checking the draft repeatedly as another way the task was being delayed.
[91] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 11-11: After the connection resumed, the discussion returned to the same task and to evening routines.
[92] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 11-11: Discussed keeping the wind-down routine brief and repeatable.
[93] BH-D106, BH-D106_telehealth_2026-01-21.txt, lines 11-11: Rowan described one night of improved sleep followed by a night of prolonged wakefulness.
[94] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 9-9: Facilitator encouraged a limited, planned review period and a stopping point.
[95] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 9-9: The patient contributed an example to the discussion after the break.
[96] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 9-9: The session addressed translating a broad intention into one observable action. Members practiced reducing a complicated task to an action that could be completed in a few minutes and identifying the cue that would prompt it. Rowan joined the discussion after it had begun; the arrival field is maintained in the attendance register. Rowan used opening a work calendar as an example and described concern that seeing outstanding items would become overwhelming. Facilitator encouraged a limited, planned review period and a stopping point. The patient contributed an example to the discussion after the break.
[97] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 11-11: Reviewed the current approach of helping Rowan break a difficult task into a manageable first step.
[98] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 11-11: I will continue to address avoidance and coping within scheduled therapy.
[99] BH-D109, BH-D109_care_coordination_2026-01-23.txt, lines 9-9: The outside social worker reported that Rowan had asked for help understanding whom to contact about a gradual return schedule.
[100] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 11-11: We practiced a brief response that acknowledged the request and asked for a limited discussion of options. Used a role-play to identify when Rowan shifted from asking a question into apologizing or trying to explain every possible difficulty. Rowan was able to return to the main request with prompting. Nora Ellis participated directly in the clinical work and helped rehearse a grounding cue to use before sending the response.
[101] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 13-13: The patient remained attentive and collaborative, although hesitant about completing the task outside the office.
[102] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 13-13: Continue work on avoidance and the bedtime routine.
[103] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 13-13: Discussed maintaining scheduled treatment contact during the return-to-work planning period and bringing the response draft to the next visit if the patient remained stuck.
[104] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 12-12: I supported a grounding exercise using contact with the chair and feet on the floor, then helped the patient return to the planned wording. The patient could use the cue during the rehearsal but remained uncertain about using it independently when anxious.
[105] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 14-14: Clinical presentation remained consistent with ongoing anxiety, low mood, and functional difficulty around work demands.
[106] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 9-9: Rowan described sending a short message to the supervisor and receiving a request to discuss possible next steps. The reply reduced one uncertainty but also brought up worry about being asked for commitments the patient might not be able to meet. Rowan continued to postpone choosing a time for the conversation.
[107] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 9-9: Sleep remained uneven, with difficulty settling on nights when work-related thoughts became repetitive.
[108] BH-D110, BH-D110_individual_primary_record_2026-01-26.txt, lines 13-13: No current suicidal ideation was reported.
[109] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 10-10: Rowan discussed difficulty moving from a supervisor's reply to arranging the next conversation.
[110] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 10-10: The patient anticipated becoming overwhelmed if several work issues were raised at once.
[111] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 12-12: Rowan recognized a tendency to keep editing a message after the essential point was already clear.
[112] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 12-12: The discussion also addressed how repetitive planning at night affected settling for sleep.
[113] BH-D111, BH-D111_individual_second_record_2026-01-26.txt, lines 14-14: Rowan was engaged with the treatment team and described a wish to resume a steadier routine.
[114] BH-D108, BH-D108_final_attendance_and_cancellation_register.txt, lines 18-18: January 28 scheduling entry: Cancellation received from patient January 28, 08:12. Rowan reported a personal scheduling conflict.
[115] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 14-14: The facilitator helped identify a specific question to ask rather than trying to anticipate every possible concern. Rowan participated in the paired rehearsal and accepted feedback about keeping the request brief.
[116] BH-D107, BH-D107_group_activity_records_2026-01-22_and_29.txt, lines 14-14: Members identified an initial effort, what made follow-through difficult, and one adjustment for the next attempt. Rowan reported opening the work calendar but delaying a follow-up conversation.
[117] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 11-11: Together, they identified a recurring pattern in which a reminder about contacting work led to a lengthy discussion, followed by Rowan withdrawing from the task.
[118] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 11-11: Facilitated a rehearsal in which Casey first asked whether Rowan wanted company, practical help, or a later check-in. Rowan practiced requesting a specific kind of help and naming when a reminder felt overwhelming.
[119] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 10-10: Rowan was alert, organized in conversation, and able to describe the follow-up plan.
[120] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 10-10: No new acute safety issue emerged in this visit.
[121] BH-D115, BH-D115_symptom_measure_review_2026-01-30.txt, lines 10-10: Rowan shows partial improvement, with persistent avoidance and meaningful functional impact around returning to work.
[122] BH-D115, BH-D115_symptom_measure_review_2026-01-30.txt, lines 10-10: The patient has taken some initial steps, including drafting and sending a message, but continues to delay follow-up and becomes anxious when a task expands beyond a narrowly defined action.
[123] BH-D115, BH-D115_symptom_measure_review_2026-01-30.txt, lines 10-10: Sleep disruption remains an intermittent barrier to establishing a steadier daytime routine.
[124] BH-D115, BH-D115_symptom_measure_review_2026-01-30.txt, lines 12-12: Continued treatment is appropriate given the remaining difficulties with follow-through and work-related functioning.
[125] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 9-9: Rowan's partner, Casey Mercer, arrived first. During the initial interval, Casey described uncertainty about when reminders helped and when they seemed to increase Rowan's sense of pressure. Rowan was not present for that portion. The discussion focused on Casey's observations and questions about supporting the agreed approach tasks.
[126] BH-D113, BH-D113_family_therapy_2026-01-30.txt, lines 13-13: Rowan remained anxious about the work conversation but could explain the intended first step. The patient reported that having a limited plan felt more manageable.
[127] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 8-8: Rowan reported taking the medication as prescribed and did not describe a new adverse effect.
[128] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 8-8: Mood felt less persistently low than earlier in the month, although anxiety remained noticeable when anticipating contact with work.
[129] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 8-8: Sleep was still variable.
[130] BH-D114, BH-D114_medication_management_2026-01-30.txt, lines 10-10: The patient denied current suicidal thoughts.
[131] BH-D115, BH-D115_symptom_measure_review_2026-01-30.txt, lines 8-8: The patient continued to endorse sleep difficulty and trouble sustaining usual activities, with fewer days of pervasive low mood than reported at intake.
