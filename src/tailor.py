"""
  tailor.py — Tailor the base resume for a specific job using an LLM.
                                             
  Supports three providers (auto-detected from .env):
    - "groq"      — Groq API with Llama 3 (FREE, no credit card)                                              
    - "gemini"    — Google Gemini 2.0 Flash (FREE via Google AI Studio)                                      
    - "anthropic" — Anthropic API (paid)                                                                      
                                                                                                             
  Provider is selected automatically in main.py based on which API key is set.                                
  """                                                      
                                                                                                             
import re 
import time                                                                                                
                                                                                                             
SYSTEM_PROMPT = """You are an expert technical resume writer with deep knowledge of the software engineering
   job market.                            
                                                                                                             
  Your task is to substantially rewrite a candidate's resume to target a specific role. Follow these rules    
  strictly:                                                                                                  
                                                                                                             
  1. REORDER SECTIONS: Put the most relevant sections first for this role. For ML roles, lead with ML        
  projects. For DevOps, lead with infrastructure work. For Frontend, lead with UI projects.
                                                                                                             
  2. MIRROR LANGUAGE: Use the exact keywords, tools, and phrases from the job description. If the job says    
  "FastAPI microservices", the resume should say "FastAPI microservices" (not just "web services"). If it
  mentions Kafka, highlight async/messaging experience explicitly.                                            
                                                                                                             
  3. REWRITE BULLET POINTS: Transform generic bullets into role-specific ones. Quantify outcomes. Use action
  verbs the job description uses.                                                                            
                                                           
  4. ADJUST PROFESSIONAL SUMMARY: Rewrite the summary from scratch to speak directly to this specific role and
   company. Mention the role title and key requirements.
                                                                                                             
  5. DE-EMPHASIZE IRRELEVANT SKILLS: Move unrelated technologies lower or remove them from the skills section.
   A Frontend role should not lead with ML frameworks.
                                                                                                             
  6. KEEP FACTS ACCURATE: Do not invent experiences or companies. Only reframe and reorder existing          
  experiences.                            
                                                                                                             
  Output the complete tailored resume as plain text using the following section headers exactly:              
  - ALEX J. MORGAN (name line)            
  - [contact line]                                                                                            
  - PROFESSIONAL SUMMARY                                                                                      
  - TECHNICAL SKILLS                      
  - WORK EXPERIENCE                                                                                          
  - PROJECTS                                                                                                  
  - EDUCATION
  - CERTIFICATIONS & ACTIVITIES                                                                              
                                                           
  The resume must be noticeably and meaningfully different from the base resume. A reviewer comparing two
  tailored resumes side-by-side should immediately see different emphasis, ordering, and language."""        
   
                                                                                                             
def _build_user_message(base_resume_text: str, job: dict) -> str:
      requirements_list = "\n".join(f"  - {r}" for r in job.get("requirements", []))                          
      nice_to_have_list = "\n".join(f"  - {n}" for n in job.get("nice_to_have", []))
                                             
      return f"""TARGET ROLE: {job['title']} at {job['company']}
  JOB URL: {job['url']}                                                                                      
                                                                                                             
  JOB DESCRIPTION:                                                                                            
  {job['description']}                                                                                        
                                                                                                             
  REQUIREMENTS:                                            
  {requirements_list}
                                                                                                             
  NICE TO HAVE:
  {nice_to_have_list}                                                                                        
                                                           
  ---

  BASE RESUME:
  {base_resume_text}

  ---                                        
                                         
  Now produce the tailored resume for the {job['title']} role. Follow all instructions from your system
  prompt. Output only the resume text — no preamble, no explanation."""                                      
   
                                                                                                             
def _tailor_groq(base_resume_text: str, job: dict, api_key: str) -> str:
      """Call Groq API with Llama 3.3 70B (free tier, no credit card required)."""                            
      from groq import Groq                                                                                  
                                         
      client = Groq(api_key=api_key)                                                                          
      user_message = _build_user_message(base_resume_text, job)                                              
                                             
      response = client.chat.completions.create(                                                              
          model="llama-3.3-70b-versatile",                  
          messages=[                                                                                          
              {"role": "system", "content": SYSTEM_PROMPT},
              {"role": "user", "content": user_message},                                                      
          ],                                                
          max_tokens=2048,
          temperature=0.7,                                                                                    
      )
      return response.choices[0].message.content.strip()                                                      
                                                           
                                             
def _parse_retry_delay(error_str: str, default: int = 60) -> int:                                          
      """Extract the retry delay in seconds from a 429 error message."""
      match = re.search(r"retry[^0-9]*(\d+)", error_str, re.IGNORECASE)                                      
      return int(match.group(1)) + 5 if match else default  
                                                                                                             
                                                           
def _tailor_gemini(base_resume_text: str, job: dict, api_key: str) -> str:                                  
      """Call Google Gemini 2.0 Flash via AI Studio free tier."""
      from google import genai                                                                                
      from google.genai import types                        
                                                                                                             
      client = genai.Client(api_key=api_key)                
      user_message = _build_user_message(base_resume_text, job)

      for attempt in range(4):                                                                                
          try:
              response = client.models.generate_content(                                                      
                  model="gemini-2.0-flash",                
                  contents=user_message,  
                  config=types.GenerateContentConfig(
                      system_instruction=SYSTEM_PROMPT,                                                      
                      max_output_tokens=2048,
                      temperature=0.7,                                                                        
                  ),                                        
              )
              return response.text.strip()                                                                    
          except Exception as e:
              error_str = str(e)                                                                              
              if "429" in error_str and attempt < 3:        
                  wait = _parse_retry_delay(error_str)
                  print(f"  Rate limited — waiting {wait}s then retrying (attempt {attempt + 1}/4)...")
                  time.sleep(wait)            
              else:                                                                                          
                  raise
                                                                                                             
                                                           
def _tailor_anthropic(base_resume_text: str, job: dict, api_key: str) -> str:                              
      """Call Anthropic API (paid)."""                      
      import anthropic                        
                                         
      client = anthropic.Anthropic(api_key=api_key)
      user_message = _build_user_message(base_resume_text, job)                                              
      message = client.messages.create(
          model="claude-3-5-sonnet-20241022",                                                                
          max_tokens=2048,                                  
          system=SYSTEM_PROMPT,
          messages=[{"role": "user", "content": user_message}],                                              
      )                                      
      return message.content[0].text.strip()                                                                  
                                                           
                                                                                                             
def tailor_resume(
      base_resume_text: str,                                                                                  
      job: dict,                                            
      api_key: str,
      provider: str = "groq",
  ) -> str:                                  
      """                                
      Tailor the base resume for a specific job using the selected LLM provider.
                                                                                                             
      Args:
          base_resume_text: Raw text of the candidate's base resume                                          
          job: Merged job dict from parser (title, description, requirements, nice_to_have)
          api_key: API key for the selected provider
          provider: "groq" (default, free), "gemini" (free), or "anthropic" (paid)
                                             
      Returns:                                                                                                
          Tailored resume as a plain text string
      """                                                                                                    
      if provider == "groq":                                
          return _tailor_groq(base_resume_text, job, api_key)                                                
      elif provider == "gemini":                            
          return _tailor_gemini(base_resume_text, job, api_key)
      elif provider == "anthropic":      
          return _tailor_anthropic(base_resume_text, job, api_key)
      else:                                                                                                  
          raise ValueError(f"Unknown LLM provider: '{provider}'. Choose 'groq', 'gemini', or 'anthropic'.")