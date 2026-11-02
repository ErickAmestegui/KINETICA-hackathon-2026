# Hackathon requirements audit — 2026-11-02

This register separates verified organizer requirements from local preparation goals. No entry was submitted, terms accepted, account changed, project deployed or public upload made during this audit.

## Verified official sources

- [Meta event page](https://dev.meta.ai/events/global-hackathon), read 2026-11-02.
- [Meta / Cerebral Valley public event page](https://events.cerebralvalley.ai/e/meta-ai-developer-hackathon), read 2026-11-02.
- [Hackathon Terms & Conditions (“Official Rules”) and Event Waiver](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver), document dated October 25, 2026, read in the rendered browser 2026-11-02. The text reader initially showed Loading; waiting for JavaScript in Playwright revealed the complete official text. This supersedes the October 29 access limitation.
- [Official submission portal](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit), linked by those rules. The first audit reached login. During final preparation on 2026-11-02, an existing authenticated session exposed the complete Submit Project form. No credentials were entered, field edited, consent accepted or submission sent. See [exact fields and deliverables](SUBMISSION_FORM.md).

Private, unedited browser accessibility snapshots preserve both the first login-only inspection and the later authenticated form. Current files include `output/submission-authenticated-form-2026-11-02.yml` and `output/submission-current-waiver-2026-11-02.yml`. They remain outside Git because the authenticated snapshot contains account context. The sanitized form schema `docs/submission/FORM_SCHEMA.json` is versioned in the private workspace only. These are audit captures, not proof of full eligibility or a submission receipt.

## Deadline and event fit

The organizer pages give **November 4, 2026 at 9:00 PM Eastern Time** for project delivery. On that date this is **November 5 at 02:00 UTC / November 4 at 22:00 Bolivia**. Conversion was independently reproduced using Windows `TimeZoneInfo`, `Eastern Standard Time` and `SA Western Standard Time`. Organizer dates may change; recheck the portal immediately before an authorized submission.

The Indie Developer track and Push the Frontier theme exist. The latter includes engineering and physical-system applications. These fit KINETICA's intended positioning, but do not establish acceptance or a score. Public application selection criteria are separate from project judging.

## Verified in the rendered Official Rules

| Item | Verified requirement / implication |
|---|---|
| Participation | Application and acceptance required; 18+ and legal majority in residence jurisdiction; geographic, sanctions and affiliation exclusions apply. Individual eligibility remains unverified. |
| Track / team | One track per participant/project. Indie teams may contain up to four; an authorized representative submits and identifies all members. |
| Meta contribution | Participants build with Meta AI products; keep authentic SAM evidence and disclose the unsuccessful Muse attempt. |
| Judging | Impact 30%; Use of Meta AI Tooling 25%; Technical Depth & Execution 20%; Demo 25%, including demo-video quality and live operation. |
| Rights | Entrants retain ownership but grant broad perpetual organizer licenses. Materials have no confidentiality assurance. Original work and third-party rights/license compliance are required; technical assistance has ownership conditions. |
| Submission destination | Cerebral Valley's project portal; authenticated form read without alteration. Public GitHub repository and 3-Minute Demo Video URL are required. |

The rules were read, not accepted on the participant's behalf. This is a requirements inventory, not a legal eligibility determination. A team representative must review the complete contract before authorization to submit.

## Authenticated form: now confirmed

Required fields: Team Name; track; problem statement; Project Description; Public GitHub Repository; 3-Minute Demo Video; use of Meta products; why Meta models matter; likelihood of building with Meta Model API; and overall opinion of Meta Model API. Team members and optional developer-feedback controls are also displayed. The unchecked materials-use consent is documented separately; no acceptance was made. See [the exact inventory](SUBMISSION_FORM.md) and prepared local answers (`docs/submission/CANDIDATE_TEXT.md`, entrant-private).

**Three-minute video and public GitHub repository are now verified form requirements**, superseding the first audit. The video field is a URL with a YouTube example, not a direct upload. No separate hosted-app URL, deck or PDF field was observed. Codec, resolution, file size, language, caption format, duration tolerance and video visibility policy remain unspecified in the inspected form. Text fields expose no maxlength, but server-side validation was not exercised.

The entrant must still approve identity/team authority, required subjective answers, rights/consents and public links. Submission/receipt behavior remains untested because nothing was sent. Saved SAM is authentic Meta contribution; successful Muse remains an internal integration goal, not an established requirement to use two Meta models.

## Source differences and release gates

The landing page lists current model names, while the rules list earlier names plus other Meta products identified on the event page. Do not assume every named model must be used. The public page still says rules will be published before October 26, but the rendered waiver now contains the actual dated rules; rely on the complete current rules and accepted-participant portal.

No conflict was found for the project deadline. The application's historical October deadline uses ET on the event page and EST in the waiver; this audit does not infer participation from either. Current project submission is after the US daylight-saving transition and the Bolivia conversion above is consistent.

Before release: verify participant eligibility/authority and contract acceptance; preserve credits/licenses and review third-party material under the organizer grant; exclude secrets/private data; obtain separate approval for public links and final submission. Eitech source lineage is now demonstrated by byte-identical official media plus decoded clip comparison: [rights audit](RELEASE_RIGHTS.md). Use [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) for the concrete remaining gates.
