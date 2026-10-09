# Responsible-Use Note: SMS Spam Filter

**Deployed model:** LinearSVM with character n-gram TF-IDF (2–5), calibrated probabilities,
threshold 0.74 chosen to minimise cost with a false positive costing 10× a false negative.
**Test performance:** precision 0.992, recall 0.908, PR-AUC 0.988; 1 of ~904 legitimate
messages blocked (0.11%), 12 of 131 spam missed. This is a post-hoc deployment check: the
pre-planned cost-based selection chose Naive Bayes + char (5 ham blocked, 8 spam missed on
test), and the SVM was deployed because Naive Bayes almost never outputs a probability
between 0.1 and 0.9. Because the test set was seen for two models, these figures are
slightly optimistic.

## 1. Harm caused by blocking legitimate messages
Blocking a legitimate message is the most serious failure of this system. A hidden
one-time passcode, bank or mobile-money alert, delivery notice or personal message can
cause financial loss or missed emergencies, while a missed spam is usually an annoyance.
This asymmetry drove the design:
- The threshold was chosen with an explicit 10:1 cost ratio, and the chosen threshold
  stayed at 0.74 for every ratio from 5:1 to 20:1.
- The deployment model was chosen partly because it blocked 1 legitimate test message
  versus 5 for Naive Bayes.
- The service's action is **"move to spam folder (user can restore)"**, never delete.
  Users must be able to review and rescue messages and mark them "not spam".
- Messages from the user's contacts and from verified short codes (banks, OTP senders,
  the network operator) should bypass the filter entirely.

The one blocked test message was a genuine job notice, pushed over the threshold mainly
by the word "Service". Legitimate senders whose messages *look* promotional (employers,
small businesses, delivery services) carry a higher risk of being filtered, so they
deserve a whitelisting or appeal route.

## 2. Message privacy
SMS content is personal data. The service:
- processes text in memory and does not log or store message content;
- returns only a score and word-level explanations to the caller.

A production deployment would also need encryption in transit (HTTPS), access control on
the API, a lawful basis and data-minimisation consistent with Zimbabwe's Cyber and Data
Protection Act, and retention limits on any messages users report as spam for retraining.
Scoring on the device itself would avoid sending messages to a server at all.

## 3. Adversarial evasion
Spammers adapt. The robustness tests showed:
- Character n-grams are far more robust than word n-grams. Under spaced or dotted
  trigger words, the margin-based word models (LinearSVM and logistic regression) fell
  to 47–57% recall, while the deployed model kept 85%.
- The most effective attack replaced digits with look-alike letters (0800 → O8OO),
  cutting recall from 0.908 to 0.824. This attacks the model's strongest signal:
  premium-rate numbers and prices.
- A disguised example ("W1NNER… C4ll O9O617Ol46l") was caught with probability 0.758,
  only just above the 0.74 threshold.
- Attacks were tested one at a time; combined disguises would likely do more damage.

Mitigations: normalise text before scoring (undo leetspeak, rejoin spaced letters,
map look-alike characters inside numbers), add disguised spam to the training data,
use sender reputation and message rate as extra signals, and retrain regularly from
user spam reports.

## 4. Language and distribution shift
The corpus was compiled in 2011 from older public sources. All the spam comes from UK
sources (the Grumbletext complaints forum and an earlier SMS spam corpus), and most of
the ham (3,375 of 4,827 messages) comes from Singaporean university students. This
creates two risks:
- **Confounding:** the model may partly have learned "Singaporean student English vs.
  UK marketing English" rather than "ham vs. spam". The strongest ham features (`i`,
  `my`, `:)`, `..`) and informal words such as "lor" and "lar" reflect this.
  Legitimate messages written in a different style could look more like spam.
- **Unseen language and content:** the model has never seen Shona, Ndebele or
  mixed-language messages; local scam patterns (e.g. fake mobile-money reversals, prize
  or job scams using local brands and ZiG/USD amounts); or modern links, URL shorteners
  and current slang.

**Observed failure:** while testing the deployed service, the account-suspension phishing
message *"Your account will be suspended within 24 hours due to suspicious activity. Click
here to secure your account immediately."* scored only 0.52 and was delivered as not spam
at the 0.74 threshold. The words "suspend" and "suspicious" never appear in the training
data, and "account" is as common in ham as in spam. The model learned old prize and
premium-rate spam, not modern smishing. As a mitigation, the service now delivers
messages scoring 0.50–0.74 with a **"possibly suspicious" warning** (notebook section 13:
on validation this warns on 7 of 12 otherwise-missed spam while warning on 4 of 904
legitimate messages and blocking none). The real fix is retraining on recent, labelled
smishing messages.

Performance on local traffic is therefore unknown and probably lower. Before deployment
the model should be evaluated on a labelled sample of local messages, with monitoring of
spam-folder restore rates (a rising rate signals more false positives) and periodic
retraining.

## 5. Explainability and its limits
The service highlights the words that most influenced each decision, using word
occlusion. This helps users and support staff understand decisions, but it has limits:
for very confident predictions, removing any single word barely changes the score, so the
highlighting shows *relative* influence rather than exact effects. Explanations describe
the model's behaviour, not the sender's intent.

## 6. Summary of safeguards
| Risk | Safeguard |
|---|---|
| Legitimate message hidden | Cost-based threshold, spam folder not deletion, restore option, sender whitelists |
| Privacy breach | No storage or logging of text, HTTPS, data-protection compliance |
| Evasion | Character n-grams, text normalisation, retraining on reported spam |
| Uncertain or unfamiliar spam | Warning band (0.50–0.74): delivered with a warning, not blocked |
| Language shift | Local evaluation before launch, monitoring, retraining on modern smishing |
| Opaque decisions | Probability shown with influential words |
