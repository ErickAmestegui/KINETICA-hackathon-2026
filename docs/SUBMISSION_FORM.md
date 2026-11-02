# Authenticated submission form — verified 2 November 2026

Source: [Cerebral Valley project portal](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit). A session was already authenticated when inspected. No login intervention was needed, no field was edited, no consent was accepted and Submit was not pressed.

This supersedes the earlier login-only inspection in the audit checkpoint. The complete read-only field inventory is in `docs/submission/FORM_SCHEMA.json` (entrant-private, not in the public repository). It contains labels/options, not account details. Private original browser snapshots remain in ignored output/. Required status was read from visible asterisks and `aria-required`; native HTML `required` attributes alone would incorrectly describe these fields as optional.

## Exact required fields observed

| Field | Type | Prepared material |
|---|---|---|
| Team Name | Text | KINETICA |
| Which track are you submitting to? | One choice | Indie Developer Track, subject to entrant approval |
| Which problem statement did you build towards? | One choice | Push the Frontier |
| Project Description | Multiline text | Entrant-private draft |
| Public GitHub Repository | URL text | Public repository URL after separate publication approval |
| 3-Minute Demo Video | URL text | Finished local MP4; hosting URL after separate upload approval |
| Describe your use of Meta products to build the submitted project | Multiline text | Prepared authentic-SAM / failed-Muse disclosure |
| Why are Meta's models important to your solution? | Multiline text | Prepared component-segmentation rationale |
| How likely are you to build with Meta Model API? | One choice | Suggested answer for final entrant review, not attributed as an established personal opinion |
| How would you describe your overall opinion of Meta Model API? | One choice | Suggested answer for final entrant review |

Team Members displays the authenticated entrant and an Add Team Member action. Account access does not prove age, residence, absence of affiliations/exclusions, team authorization or final eligibility; these declarations remain part of the entrant's final approval. No team member was added or removed.

## Additional observed fields

- Optional X post URL for consideration in Most Viral Track. It can remain empty; no public post was created.
- Optional partner-technology feedback (placeholder names Fireworks, Modal, Baseten). None was used as an inference partner in this project; do not imply otherwise.
- Recommendation scores for Meta Model API and Muse Code, each 0–5.
- Biggest obstacle; comparison with other models; most important tool-selection factor; optional free-text elaboration; switching difficulty; most likely production blocker.
- A consent checkbox granting Meta/Cerebral Valley use, publication, sharing and promotion of submitted materials. It was unchecked. The UI does not mark it `aria-required`; that is not evidence that the contract can be ignored or that server-side validation would permit an unchecked submission. No test submission was made.

All exact choice strings are in FORM_SCHEMA.json. The official UI contains some separate options whose wording appears to be split at commas; the inventory preserves what the rendered controls actually expose rather than silently rewriting them. Optional answers may be omitted rather than inventing entrant opinions or a nonexistent comparative experiment. Muse Code recommendation should remain empty: no verified Muse Code use is documented.

## Confirmed deliverables and remaining format uncertainty

- **A public GitHub repository is required.** A local ZIP alone cannot satisfy this field.
- **A three-minute demo-video link is required.** The placeholder is a YouTube URL; it does not, by itself, prove exclusive YouTube hosting.
- No direct file-upload control, hosted application URL field or separate PDF/deck requirement was observed in this form.
- The inspected text fields contain no `maxlength` attributes or visible character limits. Server-side limits were not tested; absence of an HTML limit is not a guarantee of unlimited content.
- The form does not state codec, resolution, maximum upload size, language, caption format, exact duration tolerance or public-versus-unlisted video policy. MP4/H.264/AAC with captions is our practical prepared format, not an invented organizer mandate.

Deadline remains **4 November 2026, 22:00 Bolivia / 5 November 02:00 UTC** per the official event page. Recheck immediately before any separately authorized submission.

## Contract and originality review

The [Official Rules](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver) were re-read in the rendered browser. They retain the original-work/ownership warranties, a broad organizer grant, and an express allowance for compliant open-source software/hardware. They do not explicitly resolve how that grant applies to externally authored CC BY-SA footage. See [RELEASE_RIGHTS.md](RELEASE_RIGHTS.md) for the material-specific review. Preserve third-party notices and do not certify broader ownership than the entrant has.

This inventory is a record of observed requirements, not a legal eligibility certification or entry receipt. Final entrant approval must cover account/team details, subjective required answers, rights/consents and the exact public links.
