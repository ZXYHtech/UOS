# TRAVEL_GUIDE Privacy Policy

## Storage model

This project uses a split public/private model.

Public repository artifacts may contain general destination research, generic one-day route design, public transport information, cultural/history notes, food research, aggregate visitor statistics, generic maps, and non-identifying planning logic.

The following are **private** and must never be committed as plaintext:

- exact home/origin location;
- exact travel date and exact private timing tied to the travelers;
- relationship status/history and relationship-development goal;
- private conversation scripts or relationship-specific topic sequencing;
- relationship-specific gifting timing/wording;
- any later personal preference that materially identifies either traveler.

## Encryption

- Algorithm: AES-256-GCM
- AAD context: `UOS:TRAVEL_GUIDE:PRIVATE_CONTEXT:V1`
- Repository stores ciphertext only.
- Encryption key is stored **out of repository** and is supplied to the operator in the chat.
- Key SHA-256 fingerprint: `3b3dfa32cf1bd4f7d7d7adac40e22a46038ae638ea8189e2ae906429ec6e266a`

## Decrypted working data

Agents may decrypt private inputs only in ephemeral working memory/workspace for the task that requires them. Plaintext private data must not be committed, logged to canonical UOS artifacts, or copied into public research files.

When a private deliverable is produced, its canonical repository form must be encrypted. A decrypted preview may be shown directly to the operator in chat for review, but should not be committed as plaintext.

## Statistical integrity

Visitor-age proportions, travel-purpose proportions, seasonal visitor shares, and similar statistics must be source-traceable. If exact Dujiangyan data are unavailable, use clearly labeled proxy data or state the evidence gap. Do not invent percentages.

## Relationship-content rule

Communication and gift recommendations must prioritize mutual comfort, autonomy, authenticity, and easy opt-out. They must not use deception, coercion, pressure, or manipulative escalation techniques.
