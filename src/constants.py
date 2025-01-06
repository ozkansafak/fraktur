THREE_ROLE_USER_PROMPT = """
**Instructions**

You are to perform three steps on the provided image of a document.

**General Guidelines**:
- **Accuracy**: Capture all text elements exactly as they appear. Do **NOT** summarize or skip content, including index or table of contents pages.
- **Paragraph Integrity**: Transcribe paragraphs as cohesive blocks. Do not add carriage returns (`\\n`) at the end of each line unless explicitly present.
- **Separator**: After completing each step, print the following separator line: "-----"

**Step 1: OCR Transcription in to Raw German Text**

Task: Transcribe the entire text from the image into German, including all Fraktur characters.

**Instructions**:
1. **Accuracy**: 
   - Faithfully transcribe all text elements **WITHOUT ANY SUMMARIZATION** even if the page consists of dense repetitive looking text. 
   - Don't repetitively extract the same letter or the same '.' character unlike in the original document.

2. **Page Number Detection**:
   - Identify the **current page number** written at the **very top or bottom** of the page being transcribed.
   - Wrap only this number in `<pageno></pageno>` tags (e.g., `<pageno>13</pageno>` or `<pageno>XII</pageno>`).
   - **Caution**:
     - Numbers listed in a **Table of Contents** or an **Index** page should **never** be wrapped in `<pageno>` tags, as they refer to other pages in the book.
     - There should be at most one `<pageno>` tag per page, (or none if no page number exists for the current page.)

3. **Formatting**: Wrap the entire transcription in `<raw_german></raw_german>` tags.

**Examples**:
- **For a regular page with a page number**:
  ```
  <raw_german>
  <pageno>16</pageno>
  Text of the current page...
  </raw_german>

**Step 2: Pageno-Header-Body-Footer Analysis**

Task: Structure the transcription from Step 1 into `<pageno>`, `<header>`, `<body>`, and `<footer>` sections.

**Instructions**:
1. **Categorization**:
   - **Header**: Wrap chapter titles or section headings in `<header></header>` tags.
   - **Body**: Wrap the main text in `<body></body>` tags.
   - **Footer**: Wrap footnotes in `<footer></footer>` tags. If no footer exists, omit this section.
   - **Page Number**: Include the `<pageno>` tag at the start of the transcription if a page number was detected in Step 1.
2. **Formatting**: Wrap the structured transcription in `<german></german>` tags.
3. **Caution**:
   - Do not summarize, skip, or alter the raw_german content. Your task is to **faithfully copy** the extracted text from Step 1 and assign the correct section tags.
   - Avoid placeholder outputs such as:
     ```
     <body>[Same content as above, maintaining all structure and formatting]</body>
     ```
     or
     ```
     <body>[continued content...]</body>
     ```

**Step 3: Translation (German to English)**

Task: Translate the structured German text from Step 2 into English.

**Instructions**:
1. **Faithfulness**: Translate the text faithfully, maintaining its style, tone, and structure.
2. **Formatting**: Retain all `<pageno>`, `<header>`, `<body>`, and `<footer>` tags. Wrap the translated text in `<english></english>` tags.

**Example Output**:

<raw_german>
<pageno>XII</pageno>
... (transcribed German text) ...
</raw_german>
-----
<german>
<pageno>XII</pageno>
<header>Kapitel I: Einführung</header>
<body>Dies ist der Haupttext des Dokuments.</body>
<footer>Fußnote 1: Zusätzliche Informationen.</footer>
</german>
-----
<english>
<pageno>XII</pageno>
<header>Chapter I: Introduction</header>
<body>This is the main text of the document.</body>
<footer>Footnote 1: Additional information.</footer>
</english>

"""

THREE_ROLE_SYSTEM_PROMPT = """You have three roles:

1. **OCR Transcription Assistant**:
   - Accurately transcribe text from images, including Fraktur characters, and ensure no content from the original page is missed. Do not attempt to summarize content at your own will. Transcribe the input fraktur document.

2. **Text Structuring Expert**:
   - Categorize the transcribed text into `<pageno>`, `<header>`, `<body>`, and `<footer>` sections based on its structure and context. Do not attempt to summarize content. Copy the transcribed text in its entirety, only inserting the appropriate tags into the text.

3. **German to English Translator**:
   - Translate the structured text faithfully, staying loyal to the style and character of the original German text.
"""


FRAGMENTED_SENTENCES_PROMPT = f"""**Task Overview**
In the **Given Data** section below, you are presented the translation of `<german_page_1>` into `<english_page_1_old>`. Your objective is to address any issues caused by sentences that span across `<german_page_1>` and `<german_page_2>`.

------------------

**Chain of Thought Reasoning**
1. **Identify Potential Fragment 1 (The last sentence at the very bottom of `<german_page_1>`)**:
   - Extract the portion of German text at the end of `<german_page_1>` that may or may not be a complete sentence on its own.
   - This German piece of text is the candidate for `fragment_1`.
   - Output `fragment_1` inside `<fragment_1>...</fragment_1>` tags.

2. **Identify Potential Fragment 2 (The first sentence at the very top of `<german_page_2>`)**:
   - Extract the portion of German text at the top of `<german_page_2>` that appears to complete the thought or grammatical structure of `fragment_1`.
   - This German piece of text is the candidate for `fragment_2`. Include **only** the text necessary to complete `fragment_1` into a single coherent sentence.
   - Output `fragment_2` inside `<fragment_2>...</fragment_2>` tags.

3. **Reasoning and Validation**:
   - **Definition of a Complete Sentence**: 
       - A sentence is considered complete and coherent if:
         - It has a coherent grammatical structure.
         - It expresses a complete thought.
         - And it mostly should end with clear punctuation like a period, question mark, or exclamation mark (but OCR errors are possible)

   - **Evaluation Steps**:
      - Compare `fragment_1` and `fragment_2`:
         - Does `fragment_2` logically and grammatically continue `fragment_1`?
         - Does combining the two fragments form a complete sentence, where both `fragment_1` and `fragment_2` are grammatically incomplete or incoherent by themselves but combine into a valid sentence?

   - **Default to `<fragment_2></fragment_2>` if in doubt**:
      - If you are uncertain whether `fragment_2` logically or grammatically continues `fragment_1`, assume there is **no valid fragmentation**.

   - Ensure that `fragment_2` contains only the portion necessary to complete `fragment_1`.
   - Think out loud. Output your reasoning process and wrap your thoughts in `<thinking>...</thinking>` tags.

4. **Combine Fragments (if valid)**:
   - If the fragments align and validation succeeds, combine them into a coherent, grammatically correct sentence.
   - If they do not align or either fragment is missing, conclude that there is no valid fragmentation.
   - Again, think out loud. Output your decision inside `<decision>...</decision>` tags.

5. **Ignore Fragmented Sentence at the Top of `<german_page_1>`**:
   - If `<german_page_1_top_fragment_to_be_ignored>` is present in the **Given Data**, this fragment belongs to the top of `<german_page_1>` and has already been translated into `<english_page_1_old>`.
   - Exclude the English translation of this fragment in the final output.

**Caution**:
- Carry over the content of `<english_page_1_old>` exactly as provided, except for necessary updates related to `fragment_1` and `fragment_2`.
1. Do not summarize, abbreviate, or skip any text from `<english_page_1_old>` or the fragments. 
2. Placeholder outputs such as:
     ```
     [Same content as above, maintaining all structure and formatting]
     ```
     or
     ```
     [continued content...]
     ```
     or 
     ```
     [and so on with all military abbreviations translated...]
     ```
are strictly prohibited. Transcribe or translate the full content without omission or summary.
3. Ensure that all parts of `<english_page_1_old>` not impacted by the fragmented sentences remain intact and unchanged.
4. If unsure about a portion of the content, include it verbatim rather than summarizing or skipping it.

------------------

**Output Requirements**
1. **Chain of Thought Tokens**:
   - Output your reasoning for each step inside `<thinking>...</thinking>` tags.
   - Ensure that the reasoning is clear and concise.

2. **Candidate Fragments**:
   - Fragment 1: Wrap this in `<fragment_1>...</fragment_1>` tags.
   - Fragment 2: Wrap this in `<fragment_2>...</fragment_2>` tags.

3. **Final Decision**:
   - Indicate whether the fragments align to form a coherent sentence inside `<decision>...</decision>` tags.
   - If the fragments do not align, explicitly state this in the `<decision>` tags.

4. **Final Combined Sentence**:
   Two Cases:
   - **Case 1**:
       - If the fragments align, wrap the combined sentence in `<english_page_1_new>...</english_page_1_new>` tags.
       - Include the validated German fragment from `<german_page_2>` in `<fragment_2>` tags.
   - **Case 2**:
       - If no valid fragmentation exists, output `english_page_1_old` unchanged.
       - If `fragment_2` is empty, explicitly include `<fragment_2></fragment_2>` in the output

5. **Putting it All Together**:
   - Note: `<fragment_2>` (from the top of `<german_page_2>`) is distinct and must only be included if it forms a coherent sentence with `<fragment_1>`.
   - Preserve the translation of intact sentences, i.e. do not modify the rest of `english_page_1_old`. 

------------------

**Example 1. Output for a Fragmented Sentence**

<thinking>
Step 1: Identify `fragment_1` from the bottom of `german_page_1`.
<fragment_1>Der Angriff begann früh am Morgen</fragment_1>

Step 2: Identify `fragment_2` from the top of `german_page_2`.
<fragment_2>des 10. Mai mit schwerem Artilleriefeuer.</fragment_2>

Step 3: Validate whether the fragments align:
   - `fragment_1` ends without proper punctuation, suggesting it is incomplete.
   - `fragment_2` begins with 'des 10. Mai,' which continues the context of time introduced in `fragment_1`.
   - Only the portion necessary to complete `fragment_1` was selected from `german_page_2` to form `fragment_2`.
   - Combining them forms a coherent sentence: 'Der Angriff begann früh am Morgen des 10. Mai mit schwerem Artilleriefeuer.'
<decision>The fragments align and form a coherent sentence.</decision>
</thinking>

<english_page_1_new>The attack began early in the morning on May 10th, with heavy artillery fire.</english_page_1_new>
<fragment_2>des 10. Mai mit schwerem Artilleriefeuer.</fragment_2>

------------------

**Example 2. Two Consecutive, Unfragmented Sentences**

<thinking>
Step 1: Identify `fragment_1` from the bottom of `german_page_1`.
<fragment_1>Jedenfalls ist der Umstand, daß sich General v. Falkenhayn in den überaus wichtigen Fragen des Einsatzes der Heeresreserve und der persönlichen Einflußnahme auf die Kriegsführung im Osten nicht durchsetzte, trotzdem aber in seiner Stellung als Chef des Generalstabes des Feldheeres verblieb, von folgenschwerer Bedeutung für sein ferneres Wirken gewesen.</fragment_1>

Step 2: Identify `fragment_2` from the top of `german_page_2`.
<fragment_2>I. Erwägungen und Maßnahmen der deutschen Obersten Heeresleitung.</fragment_2>

Step 3: Validate whether the fragments align:
   - `fragment_1` is a semantically coherent sentence, and it also ends with a period, further indicating it is a complete sentence.
   - `fragment_2` does not logically or grammatically continue `fragment_1`.
   - The fragments are independent and do not logically or grammatically connect into a single sentence.
<decision>The fragments do not align and do not form a single coherent sentence.</decision>
</thinking>

<english_page_1_new>In any case, the fact that General v. Falkenhayn did not prevail in the extremely important questions of the use of army reserves and personal influence on the conduct of the war in the East, but nevertheless remained in his position as Chief of the General Staff of the Field Army, was of momentous significance for his further work.</english_page_1_new>
<fragment_2></fragment_2>

------------------

**Given Data:**
<german_page_1_top_fragment_to_be_ignored>{{german_page_1_top_fragment_to_be_ignored}}</german_page_1_top_fragment_to_be_ignored>

<german_page_1>{{german_page_1}}</german_page_1>

<german_page_2>{{german_page_2}}</german_page_2>

<english_page_1_old>{{english_page_1_old}}</english_page_1_old>
"""