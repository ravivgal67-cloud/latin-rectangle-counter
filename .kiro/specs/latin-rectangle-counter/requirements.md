# Requirements Document

## Introduction

This document specifies the requirements for a Latin Rectangle Counter application. The system will provide mathematical definitions and functions to count the number of even and odd Latin rectangles for different sizes. A Latin square is a fundamental combinatorial structure, and this application will focus on normalized Latin squares and their parity properties.

## Glossary

- **Latin Square**: An n×n array filled with n distinct symbols where each symbol occurs exactly once in each row and exactly once in each column
- **Order**: The dimension n of an n×n Latin square
- **Normalized Latin Square**: A Latin square where the first row is the identity permutation (1, 2, 3, ..., n)
- **Latin Rectangle**: An r×n array (where r ≤ n) filled with n distinct symbols where each symbol occurs at most once in each row and at most once in each column
- **Sign of Latin Rectangle**: The product of the signs of all row permutations in the Latin rectangle
- **Parity**: The property of being even or odd, determined by the sign of the structure
- **Even Latin Rectangle**: A Latin rectangle with sign +1 (even parity)
- **Odd Latin Rectangle**: A Latin rectangle with sign -1 (odd parity)
- **Even Latin Square**: A Latin square with sign +1 (even parity)
- **Odd Latin Square**: A Latin square with sign -1 (odd parity)
- **Identity Permutation**: The sequence (1, 2, 3, ..., n) in natural order
- **Normalized Latin Rectangle**: A Latin rectangle where the first row is the identity permutation (1, 2, 3, ..., n); for normalized rectangles with r ≥ 2, subsequent rows are derangements relative to previous rows
- **Derangement**: A permutation where no element appears in its original position
- **System**: The Latin Rectangle Counter application

## Requirements

### Requirement 1

**User Story:** As a mathematician, I want to specify dimensions for normalized Latin rectangles, so that the system can count positive, negative, and their difference for my research.

#### Acceptance Criteria

1. WHEN a user specifies dimensions as <r, n> where 2 ≤ r ≤ n, THE System SHALL accept the input for counting normalized Latin rectangles
2. WHEN a user specifies only n, THE System SHALL count all normalized Latin rectangles for all dimensions <r, n> where 2 ≤ r ≤ n
3. WHEN a user specifies a range n1..n2, THE System SHALL count normalized Latin rectangles for all n where n1 ≤ n ≤ n2 and for all r where 2 ≤ r ≤ n
4. WHEN a user provides invalid dimensions (r > n or r < 2 or n < 2), THE System SHALL reject the input and report an error
5. WHEN a user provides a range where n1 > n2, THE System SHALL reject the input and report an error

### Requirement 2

**User Story:** As a mathematician, I want the system to generate normalized Latin rectangles internally for r ≥ 2, so that counting is accurate and efficient.

#### Acceptance Criteria

1. WHEN generating normalized Latin rectangles with r ≥ 2, THE System SHALL ensure the first row is the identity permutation (1, 2, 3, ..., n)
2. WHEN generating normalized Latin rectangles with r ≥ 2, THE System SHALL ensure each subsequent row is a valid permutation with no column conflicts
3. WHEN generating normalized Latin rectangles, THE System SHALL produce all valid structures without duplication

### Requirement 3

**User Story:** As a mathematician, I want to determine the sign and parity of generated normalized Latin rectangles, so that I can classify them as positive or negative.

#### Acceptance Criteria

1. WHEN the System generates a normalized Latin rectangle, THE System SHALL compute its sign as the product of the signs of all row permutations
2. WHEN classifying a generated Latin rectangle, THE System SHALL determine whether it is positive (sign +1) or negative (sign -1)
3. WHEN computing the sign of a row permutation, THE System SHALL use the standard definition based on the number of transpositions
4. WHEN computing the sign of a Latin rectangle with r rows, THE System SHALL multiply the signs of all r row permutations

### Requirement 4

**User Story:** As a mathematician, I want to count positive (even) and negative (odd) normalized Latin rectangles efficiently, so that I can analyze their distribution for larger dimensions.

#### Acceptance Criteria

1. WHEN counting Latin rectangles, THE System SHALL count how many are positive (even, sign +1) and how many are negative (odd, sign -1)
2. WHEN counting is complete, THE System SHALL return the count of positive rectangles, count of negative rectangles, and their difference
3. WHEN r > 2, THE System SHALL use an efficient algorithm that avoids generating all rectangles explicitly to handle larger dimensions
4. WHEN counting normalized Latin rectangles, THE System SHALL leverage the derangement structure to optimize computation

### Requirement 5

**User Story:** As a mathematician, I want the system to cache computation results, so that I can avoid recomputing counts for dimensions I have already processed.

#### Acceptance Criteria

1. WHEN a user requests counts for dimensions <r, n>, THE System SHALL check if results exist in the cache
2. WHEN cached results exist for the requested dimensions, THE System SHALL return the cached counts without recomputation
3. WHEN a user requests counts for a range or all dimensions up to n, THE System SHALL retrieve cached results where available and compute only missing entries
4. WHEN computation completes for new dimensions, THE System SHALL store the results in the cache for future use
5. WHEN the cache is persisted, THE System SHALL use a lightweight storage format suitable for tabular data

### Requirement 6

**User Story:** As a mathematician, I want to view counting results in a clear format, so that I can analyze the distribution of positive and negative normalized Latin rectangles.

#### Acceptance Criteria

1. WHEN counting completes for dimensions <r, n>, THE System SHALL display the count of positive rectangles, count of negative rectangles, and their difference
2. WHEN counting completes for multiple dimensions, THE System SHALL display results in a tabular format with columns for r, n, positive count, negative count, and difference
3. WHEN a user requests counts for only n, THE System SHALL display results for all r from 2 to n in the table
4. WHEN displaying results, THE System SHALL format numbers for readability
5. WHEN results include cached data, THE System SHALL indicate which entries were retrieved from cache


### Requirement 7

**User Story:** As a mathematician, I want a calculation view with self-explanatory input fields, so that I can easily specify dimensions and compute counts.

#### Acceptance Criteria

1. WHEN a user accesses the calculation view, THE System SHALL display self-explanatory input fields with clear labels and examples for specifying dimensions <r, n> or n alone or a range n1..n2
2. WHEN a user submits valid dimensions in calculation view, THE System SHALL initiate the counting process and display progress feedback
3. WHEN counting completes in calculation view, THE System SHALL display results in tabular format with columns for r, n, positive count, negative count, and difference
4. WHEN a user submits invalid dimensions in calculation view, THE System SHALL display clear error messages
5. WHEN results are displayed in calculation view, THE System SHALL allow the user to submit new dimension queries without refreshing the page

### Requirement 8

**User Story:** As a mathematician, I want a presentation view to display cached results, so that I can review and present previously computed data without recomputation.

#### Acceptance Criteria

1. WHEN a user accesses the presentation view, THE System SHALL display all dimension ranges that exist in the cache
2. WHEN a user selects specific dimension ranges from the cache in presentation view, THE System SHALL display the corresponding results in a presentation-ready format
3. WHEN displaying cached results in presentation view, THE System SHALL show the tabular data with r, n, positive count, negative count, and difference
4. WHEN no cached data exists, THE System SHALL inform the user in presentation view that no results are available
5. WHEN the user is in presentation view, THE System SHALL provide navigation to switch to calculation view
