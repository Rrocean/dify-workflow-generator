# Translator

**Mode:** workflow
**Version:** 0.5.0
**Total Nodes:** 3

## Description

_No description provided_

## Input Variables

_No input variables_

## Output Variables

_No output variables defined_

## Node Details

### Start (start)

**ID:** `86014f49`

**Description:** _No description_
**Output to:** 1636028c

### Translate (llm)

**ID:** `1636028c`

**Description:** _No description_
**Input from:** 86014f49
**Output to:** 5cbdbba7

### End (end)

**ID:** `5cbdbba7`

**Description:** _No description_
**Input from:** 1636028c


## Execution Flow

```
86014f49 → 1636028c → 5cbdbba7
```

## Flow Diagram

```mermaid
graph TD
    86014f49((Start)))
    1636028c[["Translate"]])
    5cbdbba7[/End/])

    86014f49 --> 1636028c
    1636028c --> 5cbdbba7
```
