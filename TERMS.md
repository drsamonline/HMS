# Terms of supply

Version: 1.0 (draft for review)
Effective: on publication
Owner: Dr Sohil Momin — sohilmomin2000@gmail.com
Changes: Initial version.

## 1. What these terms cover

These terms cover the supply of HHMS to a hospital or clinic: what you receive, what you are responsible for, and how the software and the data inside it are governed.

They sit alongside the **End User Licence Agreement** in [LICENSE](LICENSE), which governs your right to install and use the software. **Where these terms and the EULA conflict on licensing, the EULA prevails.** Nothing here grants a right the EULA does not grant.

## 2. Licence

- **Personal and evaluation use** is granted by the EULA.
- **Commercial use — including use by a clinic, hospital, firm or government body — requires a separate written licence.** Write to sohilmomin2000@gmail.com.
- Use without a valid licence is unlicensed use of the software, whatever these terms say.

## 3. What you receive

{{STATE WHAT IS SUPPLIED — installer, server binary, documentation, the version number.}}

Updates: {{what is included, or "No update obligation is undertaken."}}
Support: {{what is included, response times, or "No support obligation is undertaken unless agreed in writing."}}

## 4. Your data belongs to you

**The hospital owns its patient data.** The Licensor has no access to it: HHMS runs on your server, inside your network, with no vendor-side account, no licence server and no remote support channel that carries patient data.

That has consequences you should accept in writing:

- **You are the Data Fiduciary** under the Digital Personal Data Protection Act, 2023. You decide what is collected and why, and you answer to your patients.
- **You are responsible for backups**, for testing a restore, and for keeping copies off the server. See [PRIVACY.md](PRIVACY.md).
- **You are responsible for access control** — named accounts, roles, and removing a leaver's access the day they leave.
- **You are responsible for retention**, under your regulator's rules and the DPDP Act. The mechanics and the current gap are set out in [docs/legal/RETENTION-AND-ERASURE.md](docs/legal/RETENTION-AND-ERASURE.md).
- **You are responsible for the security of the machine** — operating-system patching, physical access to the server, and the network it sits on.

The Licensor cannot restore your data, cannot see it, and will not be given access to it.

## 5. Environment

HHMS runs on Windows or Linux on a server in your network, with client machines connecting over the LAN. The hospital provides the hardware, the network and the operating system. The software is supplied for that environment; it is not a hosted service and the Licensor operates nothing on your behalf.

## 6. Fees and payment

{{State the fee, the basis (per installation, per bed, annual), the payment terms, and the refund position. Delete this section if the licence is granted free of charge.}}

## 7. Clinical limits

HHMS is record-keeping and administration software. It does not diagnose, does not recommend treatment, and is not a medical device. Clinical responsibility rests with the treating practitioner. See [DISCLAIMER.md](DISCLAIMER.md).

## 8. Warranty and liability

The warranty disclaimer and limitation of liability are in clauses 7 and 8 of the [EULA](LICENSE) and are not restated here, so that the two documents cannot drift apart. Nothing in either limits liability for death or personal injury caused by negligence, for fraud, or for anything Indian law does not permit to be limited.

## 9. Term and termination

{{State the term, the notice period, and what happens to the data on termination. The data is the hospital's: a terminating customer must be able to take a complete export, and the Licensor's obligation is to provide the means, not the copy.}}

## 10. Governing law

These terms are governed by the laws of India. The courts at Vadodara, Gujarat have exclusive jurisdiction.

## 11. Contact

Dr Sohil Momin, Vadodara, Gujarat — sohilmomin2000@gmail.com
