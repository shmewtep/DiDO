---
title: Competency Questions
layout: single
sidebar:
        nav: "docs"
---

### Overview
* **Last Updated:** 19 Feb 2026

| ID | Competency Question | SPARQL | Status |
|----|---------------------|--------|--------|
|**DiDO-Core**|
|*Dialogue Structure*|
| CQ1| How many **participants** are involved in _dialogue_? | [CQ1.sparql](src/sparql/CQ1.sparql) | [x] |
| CQ2| What is the **textual content** of _turn_? | [CQ2.sparql](src/sparql/CQ2.sparql) | [x] |
|*Interlocutors and Roles*|
| CQ3| Which **participant** produced _turn_? | [CQ3.sparql](src/sparql/CQ3.sparql) | [x] |
| CQ4| Is **participant** a _human_ or a _software agent_? | [CQ4.sparql](src/sparql/CQ4.sparql) | [x] |
|*Temporality*|
| CQ5| Which **turn** most closely follows _turn_? | [CQ5.sparql](src/sparql/CQ5.sparql) | [x] |
| CQ6| Which **turns** occured between _time_ and _time_? | [CQ6.sparql](src/sparql/CQ6.sparql) | [x] |
| CQ7| Which **turns** overlap with _turn_? | [CQ7.sparql](src/sparql/CQ7.sparql) | [x] |
| CQ8| What is the **duration** of _dialogue_? | [CQ8.sparql](src/sparql/CQ8.sparql) | [x] |
|*Provenance*|
| CQ9| Which **dataset** is _dialogue_ from? | [CQ9.sparql](src/sparql/CQ9.sparql) | [x] |
| CQ10| What is the **ID** of _dialogue_ within its dataset? | [CQ10.sparql](src/sparql/CQ10.sparql) | [x] |
|**DiDO-Discourse**|
| CQ11| What **dialogue acts** are associated with the utterances supporting _assertion_? | | [ ] |
| CQ12| What **utterances** were made as part of a suggestion? | | [ ] |
| CQ13| Did any interlocutors agree with **utterance**? | | [ ] |
|**DiDO-Assertion**|
| CQ14| Which **interlocutor** made _assertion_? | | [ ] |
| CQ15| What **utterances** support _assertion_? | | [ ] |
| CQ16| What **utterances** did _interlocutor_ make regarding _entity_? | | [ ] |
| CQ17| What **assertions** were made regarding _entity_? | | [ ] |
| CQ18| Did **speaker** revise their initial stance on _assertion_? | | [ ] |
| CQ19| Which **assertions** did **interlocutor** support? | | [ ] |