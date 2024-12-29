THREE_ROLE_USER_PROMPT = """Instructions:
**Instructions**

You are to perform three steps on the provided image of a document.

**General Guidelines**:
- **Accuracy**: Capture all text elements exactly as they appear. Do not summarize or skip content, including index or table of contents pages.
- **Paragraph Integrity**: Transcribe paragraphs as cohesive blocks. Do not add carriage returns at the end of each line unless explicitly present.
- **Separator**: After completing each step, print the following separator line: "-----"

**Step 1: OCR Transcription**

Task: Transcribe the entire text from the image into German, including all Fraktur characters.

**Instructions**:
1. **Accuracy**: Faithfully transcribe all text elements without summarizing. Don't repetitively extract the same letter or the same '.' character unlike in the original document.
2. **Page Number Detection**: If you detect a page number, wrap it in `<pageno></pageno>` tags (e.g., Roman numerals 'XII' or Arabic numerals '13').
3. **Formatting**: Wrap the entire transcription in `<raw_german></raw_german>` tags.

**Step 2: Header-Body-Footer Analysis**

Task: Structure the transcription from Step 1 into `<header>`, `<body>`, and `<footer>` sections.

**Instructions**:
1. **Categorization**:
 - **Header**: Wrap chapter titles or section headings in `<header></header>` tags.
 - **Body**: Wrap the main text in `<body></body>` tags.
 - **Footer**: Wrap footnotes in `<footer></footer>` tags. If no footer exists, omit this section.
2. **Formatting**: Wrap the structured transcription in `<german></german>` tags.

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
   - Accurately transcribe text from images, including Fraktur characters, and ensure no content is missed or summarized.

2. **Text Structuring Expert**:
   - Categorize the transcribed text into `<pageno>`, `<header>`, `<body>`, and `<footer>` sections based on its structure and context.

3. **German to English Translator**:
   - Translate the structured text faithfully, staying loyal to the style and character of the original German text.
"""