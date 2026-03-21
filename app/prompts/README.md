# Description of LLM Prompts

## extract_all_skills.txt

**Inputs:** *{{RESUME_TEXT}}*

A prompt to instruct the LLM to extract all skills in a resume. To be used when user does not specify textual job-matching intent.

## extract_relevant_skills.txt

**Inputs:** *{{USER_INTENT}}*, *{{RESUME_TEXT}}*

A prompt to instruct the LLM to extract skills in a resume relevant to textual intent specified by the user.