# Source Data Reference Guide

## Document Information
**Document Status:** Initial Setup
**Last Updated:** June 3, 2025
**Confidentiality Notice:** This document contains confidential information intended for legal review purposes. Do not distribute without authorization.

## Introduction

This reference guide provides comprehensive information about the source data used for the positive relationship analysis. It outlines the origin, scope, format, and processing of the message data to ensure transparency and support proper interpretation of analytical findings.

## Data Source Overview

### Message Dataset Specifications

- **Source Type:** iPhone message extraction (SMS, iMessage)
- **Date Range:** [Start date] to [End date]
- **Volume:** [Number] total messages
- **Format:** CSV file with standardized fields
- **Extraction Method:** [Extraction tool/method used]

### Primary Contact Identifiers

- **Target Number 1:** 6128856087 (SMS/iMessage communications)
- **Target Number 2:** 61428856087 (SMS/iMessage communications)
- **Additional Identifier:** "TLSPayphone" (contact name in messages)
- **Related Numbers:** Various Australian mobile numbers (filtered by +61 prefix and 04 prefix)

### Data Completeness Assessment

- **Coverage Completeness:** [Assessment of date range completeness]
- **Message Thread Continuity:** [Assessment of conversation completeness]
- **Known Gaps or Limitations:** [Description of any identified data gaps]
- **Verification Methods:** [Methods used to verify data completeness]

## Data Structure and Format

### Data Fields

| Field Name | Description | Format | Notes |
|------------|-------------|--------|-------|
| timestamp | Message date and time | YYYY-MM-DD HH:MM:SS | Converted from Apple's format (seconds since 2001-01-01) |
| from_number | Phone number of sender | String | International format or device identifier |
| direction | Message direction | "incoming" or "outgoing" | From perspective of device owner |
| message_text | Content of message | String | Full text as stored in database |
| message_type | Type of message | "SMS", "iMessage", etc. | Based on service field in database |

### Message Type Distribution

- **SMS Messages:** [Number and percentage]
- **iMessage Messages:** [Number and percentage]
- **Other Message Types:** [Number and percentage]
- **Multimedia Messages:** [Handling approach description]

### Sample Data Format

```
timestamp,from_number,direction,message_text,message_type
2023-01-01 12:34:56,6128856087,incoming,"Hello, how are you doing?",SMS
2023-01-01 12:35:23,61428856087,outgoing,"I'm doing well, thank you for asking.",iMessage
```

## Data Processing Information

### Preprocessing Steps

1. **Extraction Process**
   - Database location and access method
   - Query parameters used for extraction
   - Timestamp conversion methodology

2. **Data Cleaning**
   - Handling of special characters
   - Management of multimedia content
   - Treatment of empty or corrupted messages

3. **Data Organization**
   - Chronological sorting methodology
   - Conversation threading approach
   - Handling of duplicate messages

### Data Integrity Measures

- **Validation Procedures**
  - Consistency checks performed
  - Data format verification steps
  - Completeness verification methods

- **Chain of Custody**
  - Documentation of data handling steps
  - Access controls implemented
  - Modification tracking procedures

## Accessing and Referencing Source Data

### Evidence Citation Format

When referencing specific messages in analysis documents, use the following format:
```
[Message ID]: [Date Time] - [Direction] - [First 10 words...]
Example: MSG-2023-0001: 2023-01-01 12:34:56 - incoming - "Hello, how are you doing? I wanted to..."
```

### Message Identification System

- **ID Format:** MSG-YYYY-NNNN
- **Date Component:** Year of message
- **Sequence Component:** Sequential number within year
- **Cross-Reference System:** [Description of how to trace IDs to original database]

### Source Data Access Protocols

- **Authorization Requirements:** [Who can access raw data]
- **Access Procedure:** [How to request/access raw data]
- **Usage Restrictions:** [Limitations on data use/distribution]
- **Security Measures:** [Protections in place for raw data]

## Data Limitations and Considerations

### Known Limitations

- **Technical Limitations**
  - [Description of any extraction or format limitations]
  - [Impact on data completeness or accuracy]
  - [Mitigation strategies employed]

- **Contextual Limitations**
  - [Limitations in capturing non-text elements]
  - [Challenges in interpreting without visual/audio cues]
  - [Considerations for interpretation]

### Interpretation Guidelines

- **Context Dependency**
  - Importance of considering message sequences
  - Relevance of temporal factors
  - Integration with other communication channels

- **Technical Artifacts**
  - Message splitting considerations
  - Delivery status interpretation
  - Timestamp accuracy factors

## Conclusion

This source data reference guide provides essential information for understanding the origin, structure, and processing of the message dataset used in the positive relationship analysis. Proper reference to and understanding of the source data characteristics is crucial for accurate interpretation of the analytical findings and appropriate application in legal contexts.

---

*Note: This reference guide should be consulted when reviewing analysis documents to ensure proper understanding of data sources and limitations. All evidential citations should follow the prescribed format for consistency and traceability.*

