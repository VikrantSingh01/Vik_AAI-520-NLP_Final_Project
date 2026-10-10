Final Team Project: Multi-Agent Financial Analysis System 
Due Oct 19 by 11:59pm Points 355 Submitting a file upload Attempts 0 Allowed Attempts 3
Introduction
For the final project, you and your teammates will build a real-world financial analysis system powered by agentic AI. Unlike traditional pipelines, agentic systems can reason, plan, and act, coordinating multiple specialized LLM agents to handle complex financial tasks end-to-end. Agentic AI moves beyond scripted flows: it routes tasks, critiques itself, and improves iteratively. In the real world, investment firms deploy similar multi-agent stacks to parse news, earnings, and market signals at scale—the same patterns that you will implement using the Project Requirements and Deliverable instructions further below. 

First, every student needs to read and assimilate the Groupwork Requirements and Project Timeline so you can plan accordingly.

Groupwork Requirements
The final teamwork project is an essential component of our courses in the AAI program. This project is representative of the kind of collaborative project you may work on during your career and in real-world projects. A significant portion of your final grade is drawn from your participation in this final group project, so you are strongly encouraged to work within your team and ensure that each team member contributes equally to the final project deliverables. Team members should plan to have clear and ongoing communication with other members and engage with the project and its deliverables each week. Lack of participation and engagement with both your team and your final project can result in a failing grade for the course. While these are the expectations for the project work, if you do experience difficulty with project advancement or challenges with team dynamics, contact your instructor for assistance promptly. If you are unable to perform the project as a team, contact your instructor to explore pursuing the entire final project independently.

**Note: Team members may not get the same grade on the Final Team Project, depending on each team member's level of contribution. You will complete Peer Evaluations individually and submit them in a separate assignment link in Module 7.

Project Timeline
By the end of Module 1, complete the Teammate Survey for your course instructor to place you into pre-assigned Groups of two to three members.
By the end of Module 2, locate your assigned Project Group and members. Click People on the left navigation and select the Groups tab. Use Canvas, USD Email, or Slack to connect with team members.
By the end of Module 4, designate a team representative to submit the Team Assignment, reflecting your collaborative project progress and using the Team Project Status Update Form. 
By the end of Module 7, designate a team representative to submit your final Code Notebook as a PDF or HTML file, demonstrating the project requirements.
Project Success
As the final deliverable, your team will prepare and submit a Code Notebook to document your development and execution of the project requirements summarized here:   

Agent Functions (33.8%) 
Workflow Patterns (33.8%)
Code (32.4%) 
**No extensions will be given for any of the final projects' due dates for any reason. Final projects submitted after the final due date will not be graded.

Project Background
To develop the project requirements, your team will apply and implement concepts and techniques presented across the span of the course modules. For project background, you are specifically encouraged to view Presentation 7.1 Agentic AI in advance.

Project Requirements
For the final project, you and your teammates will build an agentic AI that researches markets and demonstrates the following:  

Agent Functions (33.8%)
Build an autonomous Investment Research Agent that:

Plans its research steps for a given stock symbol.
Uses tools dynamically (APIs, datasets, retrieval).
Self-reflects to assess the quality of its output.
Learns across runs (e.g., keeps brief memories or notes to improve future analyses).
Workflow Patterns (33.8%)
Implement the following three workflow patterns: 

Prompt Chaining: Ingest News → Preprocess → Classify → Extract → Summarize
Routing: Direct content to the right specialist (e.g., earnings, news, or market analyzers).
Evaluator–Optimizer: Generate analysis → evaluate quality → refine using feedback.
Technology Requirements
Datasets & APIs
To build your Investment Research Agent, you may utilize various datasets and APIs. It is recommended to start with Yahoo Finance; you may use the other provided datasets listed below.

Yahoo Finance – pip install yfinance (prices, financials)
Financial News – Kaggle datasets, NewsAPI.org
Economic Data – FRED API (free)
Company Filings – SEC EDGAR;
Alpha Vantage (free tier)
Examples: Financial News on Kaggle, Reuters Financial News, Yahoo Finance News API
GitHub
It is required that you and your team use GitHub as a code hosting platform to manage version control and measure collaboration during this project. Creating and adding a README file to your GitHub repository is also necessary. You should follow the PEP 8Links to an external site. – Style Guide for your Python code in the final project. Not only does GitHub facilitate groupwork and streamline assessment, but embracing this approach will also equip you with a vital skill set valued in the tech industry.

Final Deliverable
Follow these guidelines to prepare your final deliverable for submission to Canvas by the end of Module 7. 

Code (32.4%)
Prepare and submit your final team Code Notebook as a document. 

Your Notebook should be readable and in PDF (preferred) or HTML format.  
Your Notebook should include your team's GitHub Repository link.
Your Notebook should include Comments to explain the project requirements:
Agent Design and Workflows
Agent Functions and Capabilities
Evaluation and Iteration
(Optional) Supplemental Report: If your team prefers, you can prepare a Supplemental Report instead of using Notebook Comments. So, for this option, in addition to submitting the Code Notebook document (PDF or HTML file), your team would also submit a Supplemental Report document (PDF or MS Word file) with details that you would have otherwise included as Comments. 

Submission
Only one team member should submit the deliverables for the team.  

If you have followed the above final deliverable guidelines, designate a team representative to submit your final Code Notebook file as a PDF (preferred) or HTML file (and Supplemental Report as a PDF file or MS Word file, if opted). 

Note: Team members may not get the same grade on the Final Team Project, depending on each team member's level of contribution. You will each submit a Peer Evaluation form individually. 

**Plagiarism, or passing another person's code/work/answers off as one's own, either by directly copying or even paraphrasing it without proper citation, is a serious offense and can result in sanctions, including grade reductions, course failures, and even expulsion from the university. For more information, please see the USD Code of Honor.Links to an external site.

This assignment has Turnitin enabled for submissions, which means that your instructor will obtain a Similarity Report that identifies specific parts of your writing that may indicate a high level of matching to external content. You are strongly encouraged to review your work without penalty by activating the Draft Coach extension in your Google Docs prior to submitting your work for final grading.

***AI-assisted tools such as ChatGPT, Gemini, and GitHub Copilot should be used to enhance your learning, not replace it. If you use any AI tools in your assignments, you must explicitly disclose, cite, and explain their contributions (e.g., comments in code, footnotes in reports). Submitting AI-generated code and answers without sufficient understanding, modification, and justification is not acceptable. Proper attribution is essential to maintain academic integrity across all courses and will help position you for future success in this field.

To understand how your work will be assessed, view the scoring rubric below.

Click the Start Assignment button above to submit your assignment.

Rubric
Final Team Project: Multi-Agent System Scoring Rubric
Final Team Project: Multi-Agent System Scoring Rubric
Criteria	Ratings	Pts
This criterion is linked to a Learning OutcomeWorkflow Patterns (33.8%)
120 pts
Meets or Exceeds Expectations
All three workflows are successfully implemented and demonstrated in the submitted code notebook (and the optional Report document, if submitted).
90 pts
Approaches Expectations
All three workflows are implemented, but missing minor details in the submitted code notebook (and/or the optional Report document, if submitted).
60 pts
Below Expectations
One workflow is not successfully implemented or demonstrated in the submitted code notebook (and/or the optional Report document, if submitted).
30 pts
Inadequate Attempt
More than one workflow is not successfully implemented or demonstrated in code notebook (and/or the optional Report document, if submitted).
0 pts
Non-Performance
Non-performance
120 pts
This criterion is linked to a Learning OutcomeAgent Functions (33.8%)
120 pts
Meets or Exceeds Expectations
All four agent functions are successfully implemented and successfully demonstrated in the code notebook (and the optional Report document, if submitted).
90 pts
Approaches Expectations
All four agent functions are implemented, but missing minor details in the code notebook (and/or the optional Report document, if submitted).
60 pts
Below Expectations
One agent function is not successfully implemented or demonstrated in the code notebook (and/or the optional Report document, if submitted).
30 pts
Inadequate Attempt
More than one agent function is not successfully implemented or demonstrated in the code notebook (and/or the optional Report document, if submitted).
0 pts
Non-Performance
Non-performance
120 pts
This criterion is linked to a Learning OutcomeCode (32.4%)
Notebook PDF or HTML (with Supplemental Report, if opted)
115 pts
Meets or Exceeds Expectations
Code submission demonstrates the successful accomplishment of all project requirements. Submitted notebook is a readable, well-structured PDF or HTML document file. Code Notebook (and/or optional Report, if submitted) includes useful Comments and relevant visualizations to demonstrate agent workflows and functions. Viable GitHub link is included in submission and is consistent with notebook details.
86.25 pts
Approaches Expectations
Code submission mostly demonstrates the accomplishment of project requirements. Submitted notebook is a readable PDF or HTML document file. Minor issues relating to code details, structure, or in notebook comments diminish communication of project requirements. (Report document, if submitted, may be minorly lacking in the same comment details). Viable Github link is included in submission.
57.5 pts
Below Expectations
Code submission is lacking in one or more major supporting details. Submitted notebook is a readable PDF or HTML document file. Github link is included. Issues in code structure or gaps in supporting code detail or comments do not provide sufficient evidence of requirements (Report document, if submitted, is lacking in the same level of required detail).
28.75 pts
Inadequate Attempt
Evidence of project requirements is not discernable from code submission. Substantial issues in submission of PDF or HTML Notebook file or required detail to evidence accomplishments. Github link may be absent or not viable (Report document, if submitted, is not consistent with code notebook or repository).
0 pts
Non-Performance
Non-performance or submitted notebook file is not a readable PDF or HTML document.
115 pts
Total Points: 355
